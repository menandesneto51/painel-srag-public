# -*- coding: utf-8 -*-
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.virology import build_virology_metrics


class VirologyTests(unittest.TestCase):
    def make_population(self, path: Path):
        rows = [{"codigo_ibge":"5103403","municipio":"Cuiabá","populacao":700000}]
        used={"510340"}
        candidate=1
        while len(rows)<142:
            prefix=f"510{candidate:03d}"
            candidate+=1
            if prefix in used:
                continue
            used.add(prefix)
            rows.append({
                "codigo_ibge":prefix+"0",
                "municipio":f"Município Teste {len(rows)}",
                "populacao":1000,
            })
        pd.DataFrame(rows).to_csv(path,index=False)

    def make_config(self,path:Path):
        cfg={
            "reference_year":2026,
            "territorial_scope":{
                "residence_uf_field":"SG_UF",
                "residence_uf_value":"MT",
                "municipality_code_candidates":["CO_MUN_RES"],
            },
            "time":{"symptom_week_field":"SEM_PRI"},
            "virology":{
                "molecular_result_field":"PCR_RESUL",
                "molecular_result_available_values":["1","2","3"],
                "molecular_conclusive_values":["1","2"],
                "molecular_detectable_value":"1",
                "influenza_positive_field":"POS_PCRFLU",
                "influenza_positive_value":"1",
                "influenza_type_field":"TP_FLU_PCR",
                "influenza_types":{"1":"Influenza A","2":"Influenza B"},
                "other_virus_positive_field":"POS_PCROUT",
                "other_virus_positive_value":"1",
                "virus_markers":{
                    "SARS-CoV-2":"PCR_SARS2",
                    "VSR":"PCR_VSR",
                    "Adenovírus":"PCR_ADENO",
                    "Metapneumovírus":"PCR_METAP",
                    "Bocavírus":"PCR_BOCA",
                    "Rinovírus":"PCR_RINO",
                    "Parainfluenza 1":"PCR_PARA1",
                    "Parainfluenza 2":"PCR_PARA2",
                    "Parainfluenza 3":"PCR_PARA3",
                    "Parainfluenza 4":"PCR_PARA4",
                    "Outro vírus respiratório":"PCR_OUTRO",
                },
                "marker_value":"1",
            },
        }
        path.write_text(json.dumps(cfg),encoding="utf-8")

    def make_sivep(self,path:Path):
        base={
            "SG_UF":"MT","CO_MUN_RES":"510340","SEM_PRI":"202610",
            "POS_PCRFLU":"2","TP_FLU_PCR":"","POS_PCROUT":"2",
            "PCR_SARS2":"","PCR_VSR":"","PCR_ADENO":"","PCR_METAP":"",
            "PCR_BOCA":"","PCR_RINO":"","PCR_PARA1":"","PCR_PARA2":"",
            "PCR_PARA3":"","PCR_PARA4":"","PCR_OUTRO":"",
        }
        rows=[]
        r=base.copy(); r.update({"PCR_RESUL":"1","POS_PCRFLU":"1","TP_FLU_PCR":"1"}); rows.append(r)
        r=base.copy(); r.update({"PCR_RESUL":"1","POS_PCROUT":"1","PCR_SARS2":"1","PCR_VSR":"1"}); rows.append(r)
        r=base.copy(); r.update({"PCR_RESUL":"2"}); rows.append(r)
        r=base.copy(); r.update({"PCR_RESUL":"1"}); rows.append(r)
        pd.DataFrame(rows).to_csv(path,sep=";",index=False)

    def test_virology_preserves_coinfection_and_unknown_detectable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            pop=root/"population.csv"; cfg=root/"config.json"; sivep=root/"sivep.csv"
            self.make_population(pop); self.make_config(cfg); self.make_sivep(sivep)

            weekly, municipal, meta=build_virology_metrics(sivep,pop,cfg)
            self.assertTrue(meta["coinfection_allowed"])
            self.assertFalse(meta["specific_virus_positivity_enabled"])
            self.assertEqual(meta["records_with_multiple_agents"],1)
            self.assertEqual(meta["detectable_without_agent"],1)

            counts=dict(zip(weekly["virus"],weekly["deteccoes"]))
            self.assertEqual(counts["Influenza A"],1)
            self.assertEqual(counts["SARS-CoV-2"],1)
            self.assertEqual(counts["VSR"],1)
            self.assertEqual(counts["Detectável sem agente codificado"],1)
            self.assertEqual(int(weekly["registros_srag"].max()),4)
            self.assertEqual(int(weekly["pcr_resultado_disponivel"].max()),4)
            self.assertEqual(int(weekly["pcr_conclusivo"].max()),4)
            self.assertEqual(int(weekly["pcr_inconclusivo"].max()),0)


if __name__=="__main__":
    unittest.main()
