"""
Zesty OS
Asset Manager
Version: 1.0

Mission 32

Maintains structured information about
devices, people, projects, brands and
other important assets.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Asset:

    name: str
    asset_type: str
    category: str
    status: str
    owner: str
    metadata: Dict[str, str]


class AssetManager:

    def __init__(self):

        self.assets = {}

    def register(self, asset: Asset):

        self.assets[asset.name.lower()] = asset

    def get(self, name: str):

        return self.assets.get(name.lower())

    def list_all(self):

        return list(self.assets.values())


if __name__ == "__main__":

    manager = AssetManager()

    manager.register(

        Asset(

            name="MacBook Air M4",

            asset_type="Device",

            category="Computer",

            status="Active",

            owner="Sanjay",

            metadata={

                "purpose": "Zesty Development",

                "location": "Goa"

            }

        )

    )

    manager.register(

        Asset(

            name="Craftsmen & Co",

            asset_type="Business",

            category="Company",

            status="Active",

            owner="Sanjay",

            metadata={

                "industry": "Bar Consultancy"

            }

        )

    )

    print(manager.list_all())