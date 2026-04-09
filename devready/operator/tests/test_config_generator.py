import pytest
import os
import sys
import json
import toml
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from devready.operator.mise_generator import MiseGenerator
from devready.operator.devcontainer_generator import DevcontainerGenerator

def test_config_generation_syntax_and_merge(tmp_path):
    # Tests requirements 6.6, 7.4, 8.7, 6.8, 7.7
    mise_gen = MiseGenerator()
    dev_gen = DevcontainerGenerator()
    
    # 1. Mise generation
    m_path = mise_gen.generate_isolation_config(str(tmp_path), {"tools": {"node": "18.0.0"}})
    with open(m_path, 'r') as f:
        m_content = f.read()
    
    # syntax verification
    cfg = [line for line in m_content.split('\n') if not line.startswith('#')]
    assert toml.loads("\n".join(cfg))["tools"]["node"] == "18.0.0"
    
    # merge test
    mise_gen.generate_isolation_config(str(tmp_path), {"tools": {"python": "3.11"}})
    with open(m_path, 'r') as f:
        merged = toml.loads("\n".join([line for line in f.read().split('\n') if not line.startswith('#')]))
    assert merged["tools"]["node"] == "18.0.0"
    assert merged["tools"]["python"] == "3.11"

    # 2. Devcontainer generation
    d_path = dev_gen.generate_isolation_config(str(tmp_path), {"tech_stack": "python", "install_cmd": "pip install -r req.txt"})
    with open(d_path, 'r') as f:
        d_parsed = json.load(f)
    assert d_parsed["image"] == "mcr.microsoft.com/devcontainers/python:3.11"
    assert 3000 in d_parsed["forwardPorts"]
    assert d_parsed["postCreateCommand"] == "pip install -r req.txt"
