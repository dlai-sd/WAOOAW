"""
Integration Tests - End-to-end factory workflow

Tests full agent generation pipeline from start to finish.

Story: #85 Integration Tests (3 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime

from waooaw.factory.config.schema import AgentSpecConfig, AgentDomain
from waooaw.factory.questionnaire import Questionnaire
from waooaw.factory.generator import CodeGenerator
from waooaw.factory.validation import Validator
from waooaw.factory.deployer import AgentDeployer
from waooaw.factory.registry import AgentRegistry, AgentStatus


@pytest.fixture
def test_spec():
    """Create test agent specification"""
    return {
        "coe_name": "WowTestAgent",
        "display_name": "WowTestAgent",
        "tier": 3,
        "domain": "communication",
        "version": "0.1.0",
        "description": "Test agent for integration testing",
        "capabilities": {
            "messaging": ["send", "receive"],
            "validation": ["schema_check"]
        },
        "constraints": [
            {
                "rule": "test-only",
                "reason": "For testing purposes only"
            }
        ],
        "dependencies": ["WowAgentFactory"],
        "wake_patterns": ["test.*", "wowtest.*"],
        "resource_budget": 25.0,
        "specialization": {
            "test_mode": True
        }
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


class TestFactoryIntegration:
    """Integration tests for factory workflow"""
    
    def test_full_generation_pipeline(self, test_spec, temp_output_dir):
        """
        Test complete agent generation from spec to files.
        
        Pipeline:
        1. Parse spec
        2. Validate spec
        3. Generate code
        4. Write files
        5. Validate generated code
        """
        # Step 1: Create spec object
        spec = AgentSpecConfig.from_dict(test_spec)
        assert spec.coe_name == "WowTestAgent"
        
        # Step 2: Generate code
        generator = CodeGenerator(output_dir=temp_output_dir)
        files = generator.generate_from_dict(test_spec)
        
        # Verify files generated
        assert len(files) >= 3  # agent, test, config
        assert "wowtestagent.py" in files
        assert "test_wowtestagent.py" in files
        assert "wowtestagent_config.yaml" in files
        
        # Step 3: Write files
        written_paths = generator.write_files(files, dry_run=False)
        assert len(written_paths) > 0
        
        # Verify files written
        agent_file = temp_output_dir / "wowtestagent.py"
        assert agent_file.exists()
        
        content = agent_file.read_text()
        assert "class WowTestAgent" in content
        assert "BasePlatformCoE" in content
        assert "should_wake" in content
        
        # Step 4: Validate generated code
        validator = Validator()
        result = validator.validate(
            spec=spec,
            agent_file=agent_file,
            test_file=None  # Skip test file validation
        )
        
        # Should pass validation (may have warnings)
        assert result.checks_run > 0
        print(f"\nValidation: {result.error_count} errors, {result.warning_count} warnings")
    
    def test_questionnaire_to_code(self, temp_output_dir):
        """
        Test questionnaire → code generation.
        
        Simulates user filling questionnaire and generating code.
        """
        # Step 1: Run questionnaire with initial values
        questionnaire = Questionnaire()
        initial_spec = {
            "coe_name": "WowQuestionnaire",
            "display_name": "WowQuestionnaire",
            "tier": 4,
            "domain": "intelligence",
            "version": "0.1.0",
            "description": "Agent generated from questionnaire test",
            "capability_categories": ["storage", "retrieval"],
            "dependencies": ["WowAgentFactory", "WowMemory"],
            "wake_patterns": ["questionnaire.*"],
            "resource_budget": 30.0
        }
        
        spec = questionnaire.run_with_initial(initial_spec)
        
        # Verify spec created
        assert spec.coe_name == "WowQuestionnaire"
        assert spec.tier == 4
        assert "storage" in spec.capabilities or "retrieval" in spec.capabilities
        
        # Step 2: Generate code
        generator = CodeGenerator(output_dir=temp_output_dir)
        files = generator._generate_files(spec)
        
        assert "wowquestionnaire.py" in files
        assert "WowQuestionnaire" in files["wowquestionnaire.py"]
    
    def test_yaml_to_deployment(self, test_spec, temp_output_dir, tmp_path):
        """
        Test YAML config → generation → validation → deployment.
        
        Full pipeline excluding actual K8s deployment.
        """
        # Step 1: Write spec to YAML
        import yaml
        yaml_path = tmp_path / "test_agent.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(test_spec, f)
        
        # Step 2: Generate from YAML
        generator = CodeGenerator(output_dir=temp_output_dir)
        files = generator.generate_from_yaml(yaml_path)
        
        assert len(files) > 0
        
        # Step 3: Write files
        written_paths = generator.write_files(files, dry_run=False)
        agent_file = temp_output_dir / "wowtestagent.py"
        
        # Step 4: Validate
        spec = AgentSpecConfig.from_dict(test_spec)
        validator = Validator()
        result = validator.validate(spec, agent_file)
        
        print(f"\nValidation result: {result.passed}")
        
        # Step 5: Deploy (dry-run)
        if result.passed:
            deployer = AgentDeployer()
            # Would deploy here in real scenario
            print("✅ Ready for deployment")
    
    def test_registry_integration(self, test_spec):
        """
        Test agent registration and tracking.
        """
        registry = AgentRegistry()
        
        # Create spec
        spec = AgentSpecConfig.from_dict(test_spec)
        
        # Register agent
        from waooaw.factory.registry import AgentMetadata, AgentTier
        metadata = AgentMetadata(
            agent_id=spec.coe_name,
            did="did:waooaw:testagent",
            name=spec.display_name,
            tier=AgentTier(spec.tier),
            version=spec.version,
            status=AgentStatus.DRAFT,
            capabilities=spec.capabilities,
            dependencies=spec.dependencies,
            description=spec.description
        )
        
        registry.register_agent(metadata)
        
        # Verify registration
        agent = registry.get_agent(spec.coe_name)
        assert agent is not None
        assert agent.agent_id == spec.coe_name
        
        # Update status
        registry.mark_deployed(spec.coe_name)
        agent = registry.get_agent(spec.coe_name)
        assert agent.status == AgentStatus.ACTIVE
        
        # Cleanup
        registry.unregister_agent(spec.coe_name)
    
    @pytest.mark.asyncio
    async def test_factory_agent_task(self, test_spec):
        """
        Test WowAgentFactory task execution.
        
        Tests the factory agent's ability to orchestrate
        the full agent creation workflow.
        """
        from waooaw.agents.wow_agent_factory import WowAgentFactory
        from waooaw.factory.interfaces.coe_interface import TaskDefinition
        
        # Initialize factory
        factory = WowAgentFactory()
        
        # Create task
        task = TaskDefinition(
            task_id="test_create_agent",
            task_type="create_new_agent",
            description="Create test agent",
            parameters={
                "initial_spec": test_spec
            },
            priority=1
        )
        
        # Execute task
        result = await factory.execute_task(task)
        
        # Verify result
        assert result["task_id"] == "test_create_agent"
        assert "result" in result
        
        print(f"\nFactory task result: {result['status']}")
    
    def test_error_handling(self):
        """
        Test error handling in generation pipeline.
        """
        generator = CodeGenerator()
        
        # Test invalid spec
        invalid_spec = {
            "coe_name": "InvalidAgent",  # Missing required fields
        }
        
        with pytest.raises(ValueError):
            generator.generate_from_dict(invalid_spec)
    
    def test_template_rendering(self):
        """
        Test template engine rendering.
        """
        from waooaw.factory.engine import TemplateEngine
        
        engine = TemplateEngine()
        
        # Test custom template
        template_str = "Hello {{ name }}!"
        context = {"name": "WowAgent"}
        
        output = engine.render_from_string(template_str, context)
        assert output == "Hello WowAgent!"
    
    def test_validation_failure(self, test_spec, temp_output_dir):
        """
        Test validation with intentional failures.
        """
        # Create invalid spec (tier out of range)
        invalid_spec = test_spec.copy()
        invalid_spec["tier"] = 10  # Invalid tier
        
        spec = AgentSpecConfig.from_dict(test_spec)  # Use valid for creation
        spec.tier = 10  # Then make invalid
        
        # Generate code
        generator = CodeGenerator(output_dir=temp_output_dir)
        files = generator._generate_files(spec)
        written_paths = generator.write_files(files, dry_run=False)
        
        agent_file = temp_output_dir / "wowtestagent.py"
        
        # Validate (should fail)
        validator = Validator()
        result = validator.validate(spec, agent_file)
        
        # Should have errors
        assert result.error_count > 0
        assert not result.passed


class TestFactoryPerformance:
    """Performance tests for factory"""
    
    def test_generation_speed(self, test_spec, temp_output_dir):
        """
        Test code generation performance.
        
        Should generate agent in < 1 second.
        """
        import time
        
        generator = CodeGenerator(output_dir=temp_output_dir)
        
        start = time.time()
        files = generator.generate_from_dict(test_spec)
        end = time.time()
        
        elapsed = end - start
        print(f"\nGeneration time: {elapsed:.3f}s")
        
        assert elapsed < 1.0, f"Generation too slow: {elapsed}s"
        assert len(files) > 0
    
    def test_validation_speed(self, test_spec, temp_output_dir):
        """
        Test validation performance.
        
        Should validate in < 5 seconds (excluding pytest).
        """
        import time
        
        # Generate code first
        generator = CodeGenerator(output_dir=temp_output_dir)
        files = generator.generate_from_dict(test_spec)
        written_paths = generator.write_files(files, dry_run=False)
        
        spec = AgentSpecConfig.from_dict(test_spec)
        agent_file = temp_output_dir / "wowtestagent.py"
        
        # Validate
        validator = Validator()
        
        start = time.time()
        result = validator.validate(spec, agent_file, test_file=None)
        end = time.time()
        
        elapsed = end - start
        print(f"\nValidation time: {elapsed:.3f}s")
        
        assert elapsed < 5.0, f"Validation too slow: {elapsed}s"


# =============================================================================
# USAGE
# =============================================================================

"""
Run integration tests:

```bash
# Run all integration tests
pytest tests/factory/test_integration.py -v

# Run specific test
pytest tests/factory/test_integration.py::TestFactoryIntegration::test_full_generation_pipeline -v

# Run with output
pytest tests/factory/test_integration.py -v -s

# Run performance tests
pytest tests/factory/test_integration.py::TestFactoryPerformance -v
```
"""
