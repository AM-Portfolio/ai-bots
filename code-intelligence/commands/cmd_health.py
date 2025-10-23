"""
Health check command handler.
"""

from orchestrator import CodeIntelligenceOrchestrator


async def cmd_health(args):
    """Handle health command"""
    orchestrator = CodeIntelligenceOrchestrator(repo_path=args.repo)
    health = await orchestrator.health_check()
    
    print("\n🏥 Health Check Results:")
    print("=" * 60)
    all_healthy = all(health.values())
    status_icon = "✅" if all_healthy else "⚠️"
    print(f"{status_icon} Overall Status: {'Healthy' if all_healthy else 'Issues Detected'}")
    print()
    for service, status in health.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {service.replace('_', ' ').title()}: {'OK' if status else 'FAILED'}")
