
class Exomiser(Benchmark):
    '''
    Exomiser

    Huggingface card: https://huggingface.co/datasets/apizza/exomiser-benchmark
    '''
    def __init__(self, name='exomiser') -> None:
        super().__init__(name)
        self.hub_name = 'apizza'
        self.dir_name = 'exomiser-benchmark'
        self.path = os.path.join(ROOT_DIR, 'benchmarks', 'datasets', self.dir_name)
        self.splits = ['validation']
        self.num_options = 4

    @staticmethod
    def custom_preprocessing(row):
        row["prompt"] = row['text']
        return row
