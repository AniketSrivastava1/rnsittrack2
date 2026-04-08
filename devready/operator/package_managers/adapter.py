import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type

class PackageManagerAdapter(ABC):
    name: str = "unknown"
    lock_files: List[str] = []
    
    @abstractmethod
    def generate_fix_command(self, action: str, package: str, version: Optional[str] = None) -> List[str]:
        pass
        
    def detect(self, project_root: str) -> bool:
        for lock_file in self.lock_files:
            if os.path.exists(os.path.join(project_root, lock_file)):
                return True
        return False
        
class PackageManagerRegistry:
    def __init__(self):
        self._adapters: Dict[str, List[Type[PackageManagerAdapter]]] = {}
        
    def register(self, tech_stack: str, adapter_class: Type[PackageManagerAdapter]):
        if tech_stack not in self._adapters:
            self._adapters[tech_stack] = []
        self._adapters[tech_stack].append(adapter_class)
        
    def detect_package_manager(self, tech_stack: str, project_root: str) -> Optional[PackageManagerAdapter]:
        adapters = self._adapters.get(tech_stack, [])
        for adapter_cls in adapters:
            adapter = adapter_cls()
            if adapter.detect(project_root):
                return adapter
        if adapters:
            return adapters[-1]()
        return None

registry = PackageManagerRegistry()
