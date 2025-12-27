#!/bin/bash
set -e

# WAOOAW Production Deployment Script
# Zero-downtime blue-green deployment to AWS ECS

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="waooaw-cluster-${ENVIRONMENT}"
BACKEND_SERVICE="waooaw-backend-${ENVIRONMENT}"
AGENT_SERVICE="waooaw-agent-${ENVIRONMENT}"
DEPLOYMENT_TIMEOUT=600  # 10 minutes

echo -e "${GREEN}🚀 WAOOAW Production Deployment${NC}"
echo "================================================"
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${AWS_REGION}"
echo "Cluster: ${CLUSTER_NAME}"
echo ""

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found${NC}"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ jq not found${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites satisfied${NC}"
}

# Get current task definition
get_current_task_definition() {
    local service_name=$1
    local task_def=$(aws ecs describe-services \
        --cluster ${CLUSTER_NAME} \
        --services ${service_name} \
        --region ${AWS_REGION} \
        --query 'services[0].taskDefinition' \
        --output text)
    echo ${task_def}
}

# Register new task definition
register_task_definition() {
    local task_def_file=$1
    local image=$2
    local service_type=$3
    
    echo "📝 Registering new task definition for ${service_type}..."
    
    # Get infrastructure outputs
    DB_HOST=$(aws rds describe-db-instances \
        --db-instance-identifier waooaw-postgres-${ENVIRONMENT} \
        --region ${AWS_REGION} \
        --query 'DBInstances[0].Endpoint.Address' \
        --output text)
    
    REDIS_HOST=$(aws elasticache describe-replication-groups \
        --replication-group-id waooaw-redis-${ENVIRONMENT} \
        --region ${AWS_REGION} \
        --query 'ReplicationGroups[0].NodeGroups[0].PrimaryEndpoint.Address' \
        --output text)
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Substitute variables in task definition
    cat ${task_def_file} | \
        sed "s/\${BACKEND_IMAGE}/${image//\//\\/}/g" | \
        sed "s/\${AGENT_IMAGE}/${image//\//\\/}/g" | \
        sed "s/\${DB_HOST}/${DB_HOST}/g" | \
        sed "s/\${REDIS_HOST}/${REDIS_HOST}/g" | \
        sed "s/\${AWS_REGION}/${AWS_REGION}/g" | \
        sed "s/\${AWS_ACCOUNT_ID}/${AWS_ACCOUNT_ID}/g" | \
        sed "s/\${EFS_ID}/${EFS_ID:-fs-xxxxxx}/g" \
        > /tmp/task-definition-${service_type}.json
    
    # Register task definition
    NEW_TASK_DEF=$(aws ecs register-task-definition \
        --cli-input-json file:///tmp/task-definition-${service_type}.json \
        --region ${AWS_REGION} \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)
    
    echo -e "${GREEN}✅ Registered: ${NEW_TASK_DEF}${NC}"
    echo ${NEW_TASK_DEF}
}

# Run database migrations
run_migrations() {
    echo "🗄️  Running database migrations..."
    
    # Get backend task definition
    TASK_DEF=$(get_current_task_definition ${BACKEND_SERVICE})
    
    # Get VPC configuration
    SUBNETS=$(aws ecs describe-services \
        --cluster ${CLUSTER_NAME} \
        --services ${BACKEND_SERVICE} \
        --region ${AWS_REGION} \
        --query 'services[0].networkConfiguration.awsvpcConfiguration.subnets' \
        --output text | tr '\t' ',')
    
    SECURITY_GROUPS=$(aws ecs describe-services \
        --cluster ${CLUSTER_NAME} \
        --services ${BACKEND_SERVICE} \
        --region ${AWS_REGION} \
        --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups' \
        --output text | tr '\t' ',')
    
    # Run migration task
    TASK_ARN=$(aws ecs run-task \
        --cluster ${CLUSTER_NAME} \
        --task-definition ${TASK_DEF} \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS}],securityGroups=[${SECURITY_GROUPS}],assignPublicIp=DISABLED}" \
        --overrides '{
            "containerOverrides": [{
                "name": "backend",
                "command": ["alembic", "upgrade", "head"]
            }]
        }' \
        --region ${AWS_REGION} \
        --query 'tasks[0].taskArn' \
        --output text)
    
    echo "⏳ Waiting for migrations to complete..."
    aws ecs wait tasks-stopped \
        --cluster ${CLUSTER_NAME} \
        --tasks ${TASK_ARN} \
        --region ${AWS_REGION}
    
    # Check exit code
    EXIT_CODE=$(aws ecs describe-tasks \
        --cluster ${CLUSTER_NAME} \
        --tasks ${TASK_ARN} \
        --region ${AWS_REGION} \
        --query 'tasks[0].containers[0].exitCode' \
        --output text)
    
    if [ "${EXIT_CODE}" != "0" ]; then
        echo -e "${RED}❌ Migration failed with exit code ${EXIT_CODE}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Migrations completed successfully${NC}"
}

# Deploy service
deploy_service() {
    local service_name=$1
    local task_def_arn=$2
    
    echo "🚢 Deploying ${service_name}..."
    
    # Update service with new task definition
    aws ecs update-service \
        --cluster ${CLUSTER_NAME} \
        --service ${service_name} \
        --task-definition ${task_def_arn} \
        --region ${AWS_REGION} \
        --force-new-deployment \
        > /dev/null
    
    echo "⏳ Waiting for deployment to stabilize (timeout: ${DEPLOYMENT_TIMEOUT}s)..."
    
    # Wait for service to stabilize
    if aws ecs wait services-stable \
        --cluster ${CLUSTER_NAME} \
        --services ${service_name} \
        --region ${AWS_REGION} \
        --cli-read-timeout ${DEPLOYMENT_TIMEOUT}; then
        echo -e "${GREEN}✅ ${service_name} deployed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ ${service_name} deployment failed or timed out${NC}"
        return 1
    fi
}

# Health check
health_check() {
    local alb_dns=$1
    local max_attempts=10
    local attempt=1
    
    echo "🏥 Running health checks..."
    
    while [ ${attempt} -le ${max_attempts} ]; do
        echo "Attempt ${attempt}/${max_attempts}..."
        
        if curl -f -s -o /dev/null "http://${alb_dns}/health"; then
            echo -e "${GREEN}✅ Health check passed${NC}"
            return 0
        fi
        
        sleep 10
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ Health check failed after ${max_attempts} attempts${NC}"
    return 1
}

# Rollback service
rollback_service() {
    local service_name=$1
    local previous_task_def=$2
    
    echo -e "${YELLOW}⏮️  Rolling back ${service_name}...${NC}"
    
    aws ecs update-service \
        --cluster ${CLUSTER_NAME} \
        --service ${service_name} \
        --task-definition ${previous_task_def} \
        --region ${AWS_REGION} \
        --force-new-deployment \
        > /dev/null
    
    aws ecs wait services-stable \
        --cluster ${CLUSTER_NAME} \
        --services ${service_name} \
        --region ${AWS_REGION}
    
    echo -e "${GREEN}✅ Rollback completed${NC}"
}

# Main deployment flow
main() {
    local backend_image="${BACKEND_IMAGE:-ghcr.io/dlai-sd/waooaw/backend:latest}"
    local agent_image="${AGENT_IMAGE:-ghcr.io/dlai-sd/waooaw/agent:latest}"
    
    echo "Images:"
    echo "  Backend: ${backend_image}"
    echo "  Agent: ${agent_image}"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Get current task definitions (for rollback)
    BACKEND_PREV_TASK=$(get_current_task_definition ${BACKEND_SERVICE})
    AGENT_PREV_TASK=$(get_current_task_definition ${AGENT_SERVICE})
    
    echo "Current task definitions:"
    echo "  Backend: ${BACKEND_PREV_TASK}"
    echo "  Agent: ${AGENT_PREV_TASK}"
    echo ""
    
    # Run database migrations
    run_migrations
    
    # Register new task definitions
    BACKEND_NEW_TASK=$(register_task_definition \
        "infrastructure/ecs/backend-task-definition.json" \
        "${backend_image}" \
        "backend")
    
    AGENT_NEW_TASK=$(register_task_definition \
        "infrastructure/ecs/agent-task-definition.json" \
        "${agent_image}" \
        "agent")
    
    # Deploy backend service
    if ! deploy_service ${BACKEND_SERVICE} ${BACKEND_NEW_TASK}; then
        echo -e "${RED}❌ Backend deployment failed${NC}"
        rollback_service ${BACKEND_SERVICE} ${BACKEND_PREV_TASK}
        exit 1
    fi
    
    # Get ALB DNS for health check
    ALB_DNS=$(aws elbv2 describe-load-balancers \
        --names waooaw-alb-${ENVIRONMENT} \
        --region ${AWS_REGION} \
        --query 'LoadBalancers[0].DNSName' \
        --output text)
    
    # Health check
    if ! health_check ${ALB_DNS}; then
        echo -e "${RED}❌ Health check failed${NC}"
        rollback_service ${BACKEND_SERVICE} ${BACKEND_PREV_TASK}
        exit 1
    fi
    
    # Deploy agent service
    if ! deploy_service ${AGENT_SERVICE} ${AGENT_NEW_TASK}; then
        echo -e "${YELLOW}⚠️  Agent deployment failed (backend still deployed)${NC}"
        rollback_service ${AGENT_SERVICE} ${AGENT_PREV_TASK}
        exit 1
    fi
    
    echo ""
    echo "================================================"
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo ""
    echo "Deployed versions:"
    echo "  Backend: ${backend_image}"
    echo "  Agent: ${agent_image}"
    echo ""
    echo "Access application:"
    echo "  URL: http://${ALB_DNS}"
    echo ""
}

# Run main function
main "$@"
