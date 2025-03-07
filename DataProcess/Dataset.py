import json
from DataProcess.Hotpotqa import HotpotQA

class Dataset:
    name = "Dataset"
    def __init__(self):
        pass

class HotpotqaDataset:
    name = "HotpotqaDataset"
    def __init__(self,dataset_path):
        self.origin_datas = self.load_json(dataset_path)
        self.tasks = [HotpotQA(datas) for datas in self.origin_datas]
    
    def load_json(self, dataset_path):
        with open(dataset_path, 'r') as file:
            origin_datas = json.load(file)
        return origin_datas

    def __len__(self):
        return len(self.datas)