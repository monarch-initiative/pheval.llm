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
            self.name = content.get("name", [])
            self.result_file = content.get("result_file", None)
            self.output_dir = content.get("output_dir", None)
            self.tmp_dir = content.get("tmp_dir", None)
            self.gold_file = content.get("gold_file", None)
            self.visualize = content.get("visualize", False)
            self.languages = content.get("languages", [])

    def __str__(self):
        return f"MalcoConfig(name={self.name}, result_file={self.result_file}, output_dir={self.output_dir}, tmp_dir={self.tmp_dir}, gold_file={self.gold_file}, visualize={self.visualize}, languages={self.languages})"
