#!/usr/bin/env python3

class ConsumerAlgorithm:
    
    def __init__(self):
        pass  

    def run(self, params: dict) -> dict:
        if "s" not in params:
            print("consumer: empty data")
            return {}
        type_name, value = params["s"]

        if type_name == "integer":
            print(f"consumer: got {value} from producer")
        else:
            print("consumer: got invalid type from producer")

        return {}


def create_algorithm_instance():
    return ConsumerAlgorithm()
