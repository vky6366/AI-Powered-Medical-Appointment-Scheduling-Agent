from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from typing import Dict
from api.config import PATIENTS_CSV

@dataclass
class PatientsService:
    def upsert_from_booking(self, payload: Dict) -> None:
        basic = {
            "name": payload.get("name", ""),
            "dob": payload.get("dob", ""),
            "email": payload.get("email", ""),
            "phone": payload.get("phone", ""),
            "insurance_carrier": payload.get("insurance_carrier", ""),
            "insurance_member_id": payload.get("member_id", "") or payload.get("insurance_member_id", ""),
            "insurance_group": payload.get("group", "") or payload.get("insurance_group", ""),
        }
        cols = ["name", "dob", "email", "phone", "insurance_carrier", "insurance_member_id", "insurance_group"]

        if PATIENTS_CSV.exists():
            dfp = pd.read_csv(PATIENTS_CSV)
            for c in cols:
                if c not in dfp.columns:
                    dfp[c] = ""
        else:
            dfp = pd.DataFrame(columns=cols)

        # match by email if present, else by (name+dob)
        import pandas as pd
        mask = pd.Series([False] * len(dfp))
        if basic["email"]:
            mask = dfp["email"].fillna("").str.lower() == basic["email"].lower()
        elif basic["name"] and basic["dob"]:
            mask = (dfp["name"].fillna("").str.lower() == basic["name"].lower()) & (
                dfp["dob"].fillna("").astype(str) == basic["dob"]
            )

        if mask.any():
            for k, v in basic.items():
                if v:
                    dfp.loc[mask, k] = v
        else:
            dfp = pd.concat([dfp, pd.DataFrame([basic])], ignore_index=True)

        dfp.to_csv(PATIENTS_CSV, index=False)
