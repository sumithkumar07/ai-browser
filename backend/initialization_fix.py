# Enhanced Module Initialization Fix
# This file ensures all enhanced modules are properly initialized

import os
import asyncio
from typing import Dict, Any, Optional

# Import all enhanced modules
from enhanced_integration_manager import EnhancedIntegrationManager
from advanced_automation_engine import AdvancedAutomationEngine  
from advanced_workflow_engine import AdvancedWorkflowEngine
from performance_optimization_engine import PerformanceOptimizationEngine
from ai_manager import get_ai_manager
from intelligent_memory_system import IntelligentMemorySystem

class ModuleInitializer:
    """Centralized module initialization system"""
    
    def __init__(self):
        self.initialized_modules = {}
        self.initialization_status = {}
    
    async def initialize_all_modules(self) -> Dict[str, Any]:
        """Initialize all enhanced modules with proper error handling"""
        
        modules_to_initialize = {
            'enhanced_integration_manager': self._init_enhanced_integration_manager,
            'advanced_automation_engine': self._init_advanced_automation_engine,
            'advanced_workflow_engine': self._init_advanced_workflow_engine,
            'performance_optimization_engine': self._init_performance_optimization_engine,
            'ai_manager': self._init_ai_manager,
            'intelligent_memory_system': self._init_intelligent_memory_system
        }
        
        initialization_results = {}
        
        for module_name, init_func in modules_to_initialize.items():
            try:
                print(f"Initializing {module_name}...")
                module_instance = await init_func()
                self.initialized_modules[module_name] = module_instance
                self.initialization_status[module_name] = "success"
                initialization_results[module_name] = "✅ Initialized"
                print(f"✅ {module_name} initialized successfully")
            except Exception as e:
                self.initialization_status[module_name] = f"failed: {str(e)}"
                initialization_results[module_name] = f"❌ Failed: {str(e)}"
                print(f"❌ {module_name} initialization failed: {e}")
        
        return initialization_results
    
    async def _init_enhanced_integration_manager(self) -> EnhancedIntegrationManager:
        """Initialize Enhanced Integration Manager"""
        manager = EnhancedIntegrationManager()
        # Start background tasks
        try:
            await manager._initialize_background_tasks()
        except:
            pass  # Background tasks are optional
        return manager
    
    async def _init_advanced_automation_engine(self) -> AdvancedAutomationEngine:
        """Initialize Advanced Automation Engine"""
        engine = AdvancedAutomationEngine()
        engine.start_background_processor()
        return engine
    
    async def _init_advanced_workflow_engine(self) -> AdvancedWorkflowEngine:
        """Initialize Advanced Workflow Engine"""
        engine = AdvancedWorkflowEngine()
        return engine
    
    async def _init_performance_optimization_engine(self) -> PerformanceOptimizationEngine:
        """Initialize Performance Optimization Engine"""
        engine = PerformanceOptimizationEngine()
        return engine
    
    async def _init_ai_manager(self):
        """Initialize AI Manager"""
        return get_ai_manager()
    
    async def _init_intelligent_memory_system(self) -> IntelligentMemorySystem:
        """Initialize Intelligent Memory System"""
        system = IntelligentMemorySystem()
        return system
    
    def get_module(self, module_name: str) -> Optional[Any]:
        """Get initialized module instance"""
        return self.initialized_modules.get(module_name)
    
    def get_status(self) -> Dict[str, str]:
        """Get initialization status of all modules"""
        return self.initialization_status.copy()

# Global initializer instance
module_initializer = ModuleInitializer()

async def initialize_all_enhanced_modules():
    """Initialize all enhanced modules - called from server.py"""
    return await module_initializer.initialize_all_modules()

def get_initialized_module(module_name: str):
    """Get an initialized module by name"""
    return module_initializer.get_module(module_name)