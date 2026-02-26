#!/bin/bash
# WAOOAW is Docker-first. Direct execution is not supported.
#
# Use: docker compose -f docker-compose.local.yml up --build

echo "=== WAOOAW is Docker-first ==="
echo ""
echo "This repository does not support running services outside Docker."
echo "Use: docker compose -f docker-compose.local.yml up --build"
echo ""
exit 1

echo ""
echo "==================================="
echo "✅ All services started!"
echo "==================================="
echo ""
echo "📍 URLs (open in browser):"
echo "   Plant Backend: http://localhost:8001/docs"
echo "   Plant Gateway: http://localhost:8000/docs"
echo "   PP Backend:    http://localhost:8015/docs"
echo ""
echo "🔍 Test Health:"
echo "   curl http://localhost:8001/health"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8015/health"
echo ""
echo "🛑 To stop all services:"
echo "   kill $PLANT_PID $GATEWAY_PID $PP_PID"
echo ""
echo "📝 Process IDs saved to .pids file"
echo "$PLANT_PID $GATEWAY_PID $PP_PID" > .pids

# Wait for user interrupt
echo "Press Ctrl+C to stop all services..."
wait
