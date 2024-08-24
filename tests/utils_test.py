from  pivot_track.lib import utils
from pathlib import Path

import pytest
import uuid

class TestLoadConfig:
    def test_empty_string(self):
        with pytest.raises(AttributeError) as e:
            utils.load_config("")
        assert str(e.value) == "Pivot Track configuration path only allows Path objects."

    def test_path_none(self):
        with pytest.raises(FileNotFoundError) as e:
            utils.load_config(None)
    
    def test_path_not_exist(self):
        with pytest.raises(FileNotFoundError) as e:
            path = Path(Path.cwd() / str(uuid.uuid4()))
            utils.load_config(path)
    
    def test_file_exists_wrong_format(self):
        assert utils.load_config(Path.cwd() / "README.md") == None
    
    def test_file_exists_right_format(self):
        assert type(utils.load_config(Path.cwd() / "config" / "config.example.yaml")) == dict