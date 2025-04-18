import os
import argparse
from simulate_server import SimulateServer
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

parser = argparse.ArgumentParser(description="Test for village")
parser.add_argument(
    "--statics_dir", type=str, default="../playground/statics", help="The statics dir"
)
parser.add_argument("--checkpoint", type=str, default="ckpt.json", help="The env file")
parser.add_argument("--step", type=int, default=5, help="The simulate step")
parser.add_argument("--stride", type=int, default=10, help="The step stride in minute")
parser.add_argument("--start", type=str, default="", help="The start time in minute")
parser.add_argument("--verbose", type=str, default="info", help="The verbose level")
args = parser.parse_args()


def get_config(agents=None):
    # agents = agents or ["Carmen Oritiz","Eddy Lin","Abigail Chen","Ayesha Khan","Carlos Gomez","Francisco Lopez","Giorgio Rossi","Latoya Williams",
    #                     "Mei Lin","Sam Moore","Tamara Taylor","Tom Moreno","Jane Moreno","Jennifer Moore","John Lin","Hailey Johnson","Arthur Burton",
    #                     "Isabella Rodriguez", "Klaus Mueller", "Maria Lopez","Rajiv Patel","Ryan Park"]
    agents = agents or ["Arthur Burton", "Maria Lopez", "Abigail Chen"]
    assets_root = os.path.join("assets", "village")
    config = {
        "maze": {"path": os.path.join(assets_root, "maze.json")},
        "agent_base": {"path": os.path.join(assets_root, "agent.json")},
        "agents": {},
    }
    for a in agents:
        config["agents"][a] = {
            "path": os.path.join(
                assets_root, "agents", a.replace(" ", "_"), "agent.json"
            )
        }
    return config


if __name__ == "__main__":
    server = SimulateServer(
        args.statics_dir, get_config(), args.checkpoint, args.start, args.verbose
    )
    server.simulate(args.step, args.stride)
