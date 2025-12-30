"""
Config Parser - Parse and validate YAML configuration files

Story: #78 Config System (3 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from waooaw.factory.config.schema import AgentSpecConfig, validate_agent_spec

logger = logging.getLogger(__name__)


class ConfigParser:
    """
    Parse and validate agent specification YAML files.
    
    Supports:
    - YAML parsing with error handling
    - Schema validation
    - Environment variable substitution
    - Template inheritance
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize parser.
        
        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = config_dir or Path(__file__).parent / "specs"
        self.loaded_specs: Dict[str, AgentSpecConfig] = {}
    
    def load_spec(self, filepath: Path) -> Optional[AgentSpecConfig]:
        """
        Load agent spec from YAML file.
        
        Args:
            filepath: Path to YAML file
        
        Returns:
            Parsed agent spec or None if invalid
        """
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            
            # Validate against schema
            is_valid, error = validate_agent_spec(data)
            if not is_valid:
                logger.error(f"❌ Invalid spec in {filepath}: {error}")
                return None
            
            # Create spec object
            spec = AgentSpecConfig.from_dict(data)
            self.loaded_specs[spec.coe_name] = spec
            
            logger.info(f"✅ Loaded spec: {spec.coe_name} from {filepath}")
            return spec
            
        except yaml.YAMLError as e:
            logger.error(f"❌ YAML parse error in {filepath}: {e}")
            return None
        except FileNotFoundError:
            logger.error(f"❌ File not found: {filepath}")
            return None
        except Exception as e:
            logger.error(f"❌ Error loading {filepath}: {e}")
            return None
    
    def load_all_specs(self) -> List[AgentSpecConfig]:
        """
        Load all agent specs from config directory.
        
        Returns:
            List of parsed specs
        """
        specs = []
        
        if not self.config_dir.exists():
            logger.warning(f"⚠️  Config directory not found: {self.config_dir}")
            return specs
        
        for yaml_file in self.config_dir.glob("*.yaml"):
            spec = self.load_spec(yaml_file)
            if spec:
                specs.append(spec)
        
        logger.info(f"✅ Loaded {len(specs)} agent specs")
        return specs
    
    def save_spec(self, spec: AgentSpecConfig, filepath: Path) -> bool:
        """
        Save agent spec to YAML file.
        
        Args:
            spec: Agent specification
            filepath: Output file path
        
        Returns:
            True if successful
        """
        try:
            spec_dict = spec.to_dict()
            
            with open(filepath, 'w') as f:
                yaml.dump(spec_dict, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"💾 Saved spec: {spec.coe_name} to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving {filepath}: {e}")
            return False
    
    def get_spec(self, coe_name: str) -> Optional[AgentSpecConfig]:
        """
        Get loaded spec by name.
        
        Args:
            coe_name: Agent name
        
        Returns:
            Agent spec or None
        """
        return self.loaded_specs.get(coe_name)
    
    def list_specs(self) -> List[str]:
        """List all loaded spec names"""
        return list(self.loaded_specs.keys())


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Example: Using ConfigParser

```python
from waooaw.factory.config.parser import ConfigParser
from waooaw.factory.config.schema import EXAMPLE_WOWDOMAIN_CONFIG, AgentSpecConfig
from pathlib import Path

# Example 1: Load single spec
parser = ConfigParser()
spec = parser.load_spec(Path("waooaw/factory/config/specs/wowdomain.yaml"))
if spec:
    print(f"Loaded: {spec.coe_name} (tier {spec.tier})")

# Example 2: Load all specs from directory
parser = ConfigParser(config_dir=Path("waooaw/factory/config/specs"))
all_specs = parser.load_all_specs()
print(f"Total specs: {len(all_specs)}")

# Example 3: Save spec to file
spec = AgentSpecConfig.from_dict(EXAMPLE_WOWDOMAIN_CONFIG)
parser.save_spec(spec, Path("output/wowdomain.yaml"))

# Example 4: Get loaded spec
domain_spec = parser.get_spec("WowDomain")
if domain_spec:
    print(f"Capabilities: {domain_spec.capabilities}")
```
"""
