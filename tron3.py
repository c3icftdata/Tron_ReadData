import json
from tronpy import Tron
from tronpy.providers import HTTPProvider
from pymongo import MongoClient

with open("configtron.json") as f:
    config = json.load(f)


client = Tron(provider=HTTPProvider(api_key=config["api_key"], endpoint_uri=config["endpoint_uri"]))
mongo = MongoClient(config["mongo_uri"])
db = mongo[config["database"]]
output_collection = db[config["collection"]]

def generate_abi(name, output_type):
    return [{
        "name": name,
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": output_type}]
    }]

for contract_address in config["contract_addresses"]:
    try:
        contract = client.get_contract(contract_address)
        results = {}

        for func_name in config["function_names"]:
            for out_type in config["output_types_to_try"]:
                try:
                    contract.abi = generate_abi(func_name, out_type)
                    result = contract.functions[func_name]()

                    if isinstance(result, int) and result > 2**63 - 1:
                        result = str(result)

                    results[func_name] = result
                    break

                except Exception:
                    continue

        if results:
            output_collection.update_one({"_id": contract_address}, {"$set": results}, upsert=True)
            print(f"\nContract: {contract_address}")
            for k, v in results.items():
                print(f"  {k}: {v}")
        else:
            print(f"\nContract: {contract_address} — No successful function calls.")

    except Exception as e:
        print(f"\nCould not process contract {contract_address}: {e}")
