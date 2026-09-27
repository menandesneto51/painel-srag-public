# -*- coding: utf-8 -*-
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.stability import estimate_delay_based_stability


class StabilityTests(unittest.TestCase):
    def make_population(self,path:Path):
        rows=[{"codigo_ibge":"5103403","municipio":"Cuiabá","populacao":700000}]
        used={"510340"}; candidate=1
        while len(rows)<142:
            prefix=f"510{candidate:03d}"; candidate+=1
            if prefix in used: continue
            used.add(prefix)
            rows.append({"codigo_ibge":prefix+"0","municipio":f"Teste {len(rows)}","populacao":1000})
        pd.DataFrame(rows).to_csv(path,index=False)

    def make_config(self,path:Path):
        cfg={
            "reference_year":2026,
            "territorial_scope":{
                "residence_uf_field":"SG_UF",
                "residence_uf_value":"MT",
                "municipality_code_candidates":["CO_MUN_RES"],
            },
            "time":{
                "symptom_week_field":"SEM_PRI",
                "symptom_date_field":"DT_SIN_PRI",
            },
            "severity":{"outcome_field":"EVOLUCAO"},
            "quality":{
                "digitization_date_field":"DT_DIGITA",
                "closure_date_field":"DT_ENCERRA",
            },
        }
        path.write_text(json.dumps(cfg),encoding="utf-8")

    def test_delay_based_stability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); pop=root/"pop.csv"; cfg=root/"cfg.json"; sivep=root/"sivep.csv"
            self.make_population(pop); self.make_config(cfg)
            rows=[]
            for delay in [1,2,3,7,8,14,15,20]:
                onset=pd.Timestamp("2026-03-01")
                rows.append({
                    "SG_UF":"MT","CO_MUN_RES":"510340","SEM_PRI":"202610",
                    "DT_SIN_PRI":onset.strftime("%d/%m/%Y"),
                    "DT_DIGITA":(onset+pd.Timedelta(days=delay)).strftime("%d/%m/%Y"),
                    "EVOLUCAO":"1",
                    "DT_ENCERRA":(onset+pd.Timedelta(days=delay+7)).strftime("%d/%m/%Y"),
                })
            pd.DataFrame(rows).to_csv(sivep,sep=";",index=False)
            result=estimate_delay_based_stability(sivep,pop,cfg,quantile=0.95)

            self.assertEqual(result["max_observed_week"],10)
            self.assertGreaterEqual(result["recommended_case_lag_weeks"],2)
            self.assertGreaterEqual(result["recommended_outcome_lag_weeks"],3)
            self.assertEqual(result["status"],"provisional_until_vintage_backtest")


if __name__=="__main__":
    unittest.main()
