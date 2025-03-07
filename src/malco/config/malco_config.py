import yaml

class MalcoConfig():
    def __init__(self, config_path):
        """
        Initialize the PhevalLLMConfig object by loading the configuration from a YAML file.

        Args:
            config_path (str): Path to the YAML configuration file.
        """
        with open(config_path, "r") as file:
            content = yaml.safe_load(file)
            self.tmp_dir = content.get("tmp_dir", None)
            self.output_dir = content.get("output_dir", None)
            self.version = content.get("version", None)
            self.gold_file = content.get("gold_file", None)
            self.result_file = content.get("result_file", None)
            self.visualize = content.get("visualize", False)
            self.name = content.get("name", [])
    
    def __str__(self):
        return (f"MalcoConfig("
                f"testdata_dir={self.testdata_dir}, "
                f"tmp_dir={self.tmp_dir}, "
                f"output_dir={self.output_dir}, "
                f"version={self.version}, gold_file={self.gold_file}, "
                f"visualize={self.visualize})")