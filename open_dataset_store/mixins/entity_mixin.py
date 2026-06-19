import pandas as pd
from typing import Dict, Optional

class EntityManagementMixin:
    def create_entity(
        self,
        entity_type: str,
        name: str = "",
        entity_id: Optional[str] = None,
        **metadata,
    ) -> str:
        index_path = self._get_entity_index_path(entity_type)
        data = self._load_json(index_path)

        if entity_id is None:
            entity_id = self._generate_entity_id(entity_type, data)

        if entity_id in data:
            raise ValueError(f"Entity '{entity_id}' already exists.")

        data[entity_id] = {"name": name, **metadata}
        self._save_json(index_path, data)
        print(f"Entity '{entity_id}' created in {entity_type}.")
        return entity_id

    def list_entities(self, entity_type: str) -> pd.DataFrame:
        data = self._load_json(self._get_entity_index_path(entity_type))
        
        entities = {k: v for k, v in data.items() if not k.startswith("__")}
        
        if not entities:
            print(f"No entities found for type '{entity_type}'.")
            return pd.DataFrame()

        df = pd.DataFrame.from_dict(entities, orient="index")
        df.index.name = "entity_id"
        df.reset_index(inplace=True)
        
        cols_at_front = ["entity_id", "name"]
        existing_front = [c for c in cols_at_front if c in df.columns]
        other_cols = [c for c in df.columns if c not in existing_front]
        
        df = df[existing_front + other_cols]
        return df

    def get_entity(self, entity_type: str, entity_id: str) -> Dict:
        data = self._load_json(self._get_entity_index_path(entity_type))
        if entity_id not in data:
            raise KeyError(f"Entity '{entity_id}' not found in {entity_type}.")
        return data[entity_id]

    def edit_entity(
        self,
        entity_type: str,
        entity_id: str,
        name: Optional[str] = None,
        **updates,
    ) -> str:
        data = self._load_json(self._get_entity_index_path(entity_type))
        if entity_id not in data:
            raise KeyError(f"Entity '{entity_id}' not found in {entity_type}.")

        if name is not None:
            data[entity_id]["name"] = name
        data[entity_id].update(updates)
        self._save_json(self._get_entity_index_path(entity_type), data)
        print(f"Entity '{entity_id}' updated.")
        return entity_id

    def delete_entity(self, entity_type: str, entity_id: str) -> str:
        index_path = self._get_entity_index_path(entity_type)
        data = self._load_json(index_path)
        if entity_id not in data:
            raise KeyError(f"Entity '{entity_id}' not found in {entity_type}.")

        del data[entity_id]
        self._save_json(index_path, data)
        print(f"Entity '{entity_id}' removed from {entity_type}.")
        return entity_id
