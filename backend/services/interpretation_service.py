"""
CXR-Explain Finding-Based Disease Interpretation Service.

Provides medically structured, evidence-based interpretations of chest radiograph
findings detected by the deep learning classifier.

Crucial Clinical & Safety Principles:
1. Radiographic findings are morphological patterns, NOT definitive pathology or diagnoses.
2. Solitary pulmonary nodules or masses have wide differentials including benign granulomas,
   hamartomas, infections, and malignancies. A classifier score is NOT a probability of cancer.
3. 2D radiographs cannot establish histological subtype, tumor grade, or invasion.
4. "No Finding" does NOT prove the absence of disease or malignancy (sub-radiographic nodules,
   early central endobronchial lesions, and micro-metastases are radiographically occult).
5. Grad-CAM displays neural attention, NOT confirmed lesion boundaries.
"""

from __future__ import annotations
from typing import Any
from backend.schemas.analysis import (
    ConditionInterpretationItem,
    FindingInterpretation,
    OverallInterpretationSummary,
    ClinicalInterpretationResponse,
)


# Knowledge Base of Evidence-Based Finding-to-Condition Associations
FINDING_KNOWLEDGE_BASE: dict[str, dict[str, Any]] = {
    "mass": {
        "name": "Mass",
        "size_definition": "Circumscribed pulmonary or mediastinal lesion > 3.0 cm in diameter.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Primary Bronchogenic Carcinoma",
                likelihood_category="Significant Differential Concern",
                pathophysiology="Malignant epithelial tumor of the lung parenchyma or tracheobronchial tree.",
                clinical_context="More prevalent in older patients with tobacco exposure, hemoptysis, or weight loss.",
                benign_vs_malignant="Malignant",
            ),
            ConditionInterpretationItem(
                condition_name="Solitary Pulmonary Metastasis",
                likelihood_category="Possible",
                pathophysiology="Secondary hematogenous seeding from known extrathoracic malignancy (e.g., colorectal, breast, renal).",
                clinical_context="Often presents as well-circumscribed 'cannonball' or solitary lesion; prior oncologic history crucial.",
                benign_vs_malignant="Malignant",
            ),
            ConditionInterpretationItem(
                condition_name="Infectious Lung Abscess / Cavitary Necrosis",
                likelihood_category="Possible",
                pathophysiology="Localized necrotic collection of pulmonary tissue caused by aspiration or pyogenic infection.",
                clinical_context="Often accompanied by air-fluid levels on lateral projection, high fevers, and productive sputum.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Benign Pulmonary Neoplasm (Hamartoma / Fibroma)",
                likelihood_category="Possible",
                pathophysiology="Disorganized benign proliferation of cartilage, fat, and epithelial tissue.",
                clinical_context="Slow-growing or stable; often exhibits 'popcorn' calcification patterns visible on high-resolution CT.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Organizing Pneumonia / Inflammatory Pseudotumor",
                likelihood_category="Possible",
                pathophysiology="Non-infectious fibroblastic intra-alveolar tissue response following pulmonary insult.",
                clinical_context="Resolves or migrates with anti-inflammatory or corticosteroid therapy; mimics neoplasia.",
                benign_vs_malignant="Benign",
            ),
        ],
        "uncertainty_statement": (
            "A radiographic mass is a macroscopic density, not a confirmed cancer diagnosis. "
            "Morphology on a 2D projection cannot differentiate benign organizing inflammation or hamartoma "
            "from malignant neoplasia without contrast-enhanced cross-sectional imaging and histological biopsy."
        ),
        "diagnostic_limitations": (
            "Standard frontal chest radiography has limited sensitivity for mediastinal invasion, chest wall invasion, "
            "lymphadenopathy, or tissue vascularity. False positives can arise from overlapping ribs, pleural thickening, or artifacts."
        ),
        "evidence_basis": "Fleischner Society Guidelines; ACR Appropriateness Criteria for Thoracic Mass Evaluation.",
        "recommended_follow_up": (
            "Immediate contrast-enhanced Chest CT recommended. Multidisciplinary pulmonary/oncology consultation "
            "with consideration of tissue acquisition (percutaneous CT-guided core biopsy or bronchoscopy with EBUS)."
        ),
    },
    "nodule": {
        "name": "Nodule",
        "size_definition": "Well-defined rounded pulmonary opacity <= 3.0 cm in diameter surrounded by aerated parenchyma.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Infectious or Post-Inflammatory Granuloma",
                likelihood_category="Very Common / High Prevalence",
                pathophysiology="Healed fibrous scar tissue following prior tuberculosis, histoplasmosis, or fungal exposure.",
                clinical_context="Accounts for over 80% of benign solitary nodules; frequently calcified and clinically stable.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Early-Stage Primary Lung Carcinoma (Adenocarcinoma / SCC)",
                likelihood_category="Differential Concern (Surveillance Warranted)",
                pathophysiology="Early neoplastic proliferation within peripheral or bronchovascular airspaces.",
                clinical_context="Risk correlates with patient age, smoking history, nodule diameter, and spiculation/growth kinetics.",
                benign_vs_malignant="Malignant",
            ),
            ConditionInterpretationItem(
                condition_name="Pulmonary Hamartoma",
                likelihood_category="Common Benign Etiology",
                pathophysiology="Benign mesenchymal lesion with cartilage and macroscopic fat.",
                clinical_context="Well-demarcated with smooth lobulated contours; stable on serial examinations.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Intrapulmonary Lymph Node",
                likelihood_category="Common Benign Etiology",
                pathophysiology="Normal lymphoid tissue situated below the carina or adjacent to pleural fissures.",
                clinical_context="Typically subpleural, ovoid or triangular, <= 12 mm in major axis.",
                benign_vs_malignant="Benign",
            ),
        ],
        "uncertainty_statement": (
            "The vast majority (>70–80%) of pulmonary nodules identified on radiologic screening are benign granulomas. "
            "A model detection of 'Nodule' establishes radiographic opacity presence only and does NOT indicate malignancy."
        ),
        "diagnostic_limitations": (
            "Sub-centimeter nodules (< 6-8 mm) have high false-negative rates on standard chest X-rays due to rib and vascular overlap. "
            "Internal nodule characteristics (calcification patterns, attenuation, ground-glass halo) require thin-slice CT for evaluation."
        ),
        "evidence_basis": "Fleischner Society 2017 Guidelines for Management of Incidental Pulmonary Nodules.",
        "recommended_follow_up": (
            "Correlation with prior thoracic imaging to evaluate temporal stability. If newly identified or indeterminate, "
            "thin-section Low-Dose CT (LDCT) or diagnostic chest CT is indicated per Fleischner Society risk-stratified intervals."
        ),
    },
    "consolidation": {
        "name": "Consolidation",
        "size_definition": "Homogeneous alveolar opacification obscuring underlying pulmonary vascular markings.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Infectious Lobar / Segmental Pneumonia",
                likelihood_category="High Likelihood",
                pathophysiology="Acute exudative replacement of alveolar gas by bacterial, viral, or atypical pathogens.",
                clinical_context="Typical clinical triad: fever, leukocytosis, and productive cough.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Pulmonary Infarction Secondary to Thromboembolism",
                likelihood_category="Critical Consideration",
                pathophysiology="Ischemic necrosis of lung parenchyma downstream of acute pulmonary arterial occlusion (Hampton hump).",
                clinical_context="Sudden onset pleuritic chest pain, dyspnea, tachycardia, or deep vein thrombosis history.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Cryptogenic Organizing Pneumonia (COP)",
                likelihood_category="Differential Consideration",
                pathophysiology="Intra-alveolar buds of granulation tissue filling bronchioles and alveoli.",
                clinical_context="Subacute cough and fever refractory to antibiotic courses; responds to steroids.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Bronchoalveolar / Invasive Mucinous Adenocarcinoma",
                likelihood_category="Atypical Malignant Mimic",
                pathophysiology="Lepidic growth of neoplastic cells lining intact alveolar walls mimicking airspace consolidation.",
                clinical_context="Persistent non-resolving consolidation despite appropriate antibiotic therapy.",
                benign_vs_malignant="Malignant",
            ),
        ],
        "uncertainty_statement": (
            "Alveolar consolidation represents fluid within airspaces but cannot distinguish pus (infection), blood (hemorrhage), "
            "edema fluid (heart failure), or malignant cells by radiograph appearance alone."
        ),
        "diagnostic_limitations": "Complete lobar opacification may mask underlying endobronchial obstructing lesions or masses.",
        "evidence_basis": "Infectious Diseases Society of America (IDSA) / American Thoracic Society (ATS) Community-Acquired Pneumonia Guidelines.",
        "recommended_follow_up": "Clinical correlation with vitals, inflammatory biomarkers (CRP, procalcitonin), and follow-up radiograph in 4-6 weeks to ensure complete resolution.",
    },
    "pneumothorax": {
        "name": "Pneumothorax",
        "size_definition": "Extravasation of gas into the pleural space with loss of negative intrapleural pressure.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Spontaneous Pneumothorax (Primary or Secondary)",
                likelihood_category="Primary Consideration",
                pathophysiology="Rupture of subpleural apical blebs (primary) or underlying parenchymal lung disease such as COPD/cystic fibrosis (secondary).",
                clinical_context="Sudden acute unilateral pleuritic chest pain and breathlessness; tall, young individuals or COPD patients.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Traumatic / Iatrogenic Pneumothorax",
                likelihood_category="Clinical Context Dependent",
                pathophysiology="Disruption of visceral or parietal pleura following thoracic trauma, central venous catheterization, or pleural biopsy.",
                clinical_context="History of mechanical intervention or blunt/penetrating chest injury.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Tension Pneumothorax",
                likelihood_category="Critical Medical Emergency",
                pathophysiology="One-way valve mechanism leading to progressive gas accumulation and mediastinal shift with hemodynamic collapse.",
                clinical_context="Severe hypotension, tracheal deviation to contralateral side, tachycardia; mandates immediate decompression.",
                benign_vs_malignant="Benign",
            ),
        ],
        "uncertainty_statement": (
            "A fine apical pleural line is the definitive sign; skin folds, clothing seams, and scapular margins frequently "
            "produce false-positive artifacts mimicking a pneumothorax."
        ),
        "diagnostic_limitations": "Supine cross-table or AP radiographs show medial/anterior gas collections (deep sulcus sign) that may be missed compared to upright PA views.",
        "evidence_basis": "British Thoracic Society (BTS) Pleural Disease Guidelines.",
        "recommended_follow_up": "Immediate clinical evaluation of patient respiratory stability. Upright expiratory radiograph or bedside ultrasound / CT if clinically uncertain.",
    },
    "pleural_effusion": {
        "name": "Pleural Effusion",
        "size_definition": "Accumulation of pathologic fluid volume within the pleural cavity blunting costophrenic angles.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Congestive Heart Failure (Transudative)",
                likelihood_category="Most Common Transudate",
                pathophysiology="Elevated hydrostatic capillary pressure causing transudation of serous fluid into pleural spaces.",
                clinical_context="Often bilateral, accompanied by cardiomegaly and interstitial pulmonary vascular redistribution.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Parapneumonic Effusion / Empyema (Exudative)",
                likelihood_category="Common Exudate",
                pathophysiology="Inflammatory exudate secondary to adjacent parenchymal pneumonia or bacterial inoculation.",
                clinical_context="Fever, pleuritic pain, associated lobar infiltrate; risk of loculation.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Malignant Pleural Effusion",
                likelihood_category="Differential Concern in Unilateral Effusions",
                pathophysiology="Direct tumor seeding of pleura or lymphatic obstruction by malignant cells (lung, breast, lymphoma).",
                clinical_context="Large, unilateral, recurrent effusion in the absence of heart failure or acute infectious symptoms.",
                benign_vs_malignant="Malignant",
            ),
        ],
        "uncertainty_statement": "Radiography confirms fluid accumulation but cannot differentiate transudative vs. exudative etiology without Light's criteria thoracentesis.",
        "diagnostic_limitations": "Subpulmonic effusions and loculated fluid collections may mimic elevated diaphragms or consolidation on single frontal views.",
        "evidence_basis": "Light's Criteria; American College of Chest Physicians (CHEST) Pleural Guidelines.",
        "recommended_follow_up": "Thoracic ultrasound for fluid characterization and guidance of diagnostic thoracentesis when clinically indicated.",
    },
    "cardiomegaly": {
        "name": "Cardiomegaly",
        "size_definition": "Cardiothoracic ratio (CTR) exceeding 0.50 (50%) on an upright posteroanterior (PA) projection.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Hypertensive Heart Disease / Left Ventricular Hypertrophy",
                likelihood_category="High Prevalence",
                pathophysiology="Longstanding pressure overload leading to myocyte hypertrophy and chamber remodeling.",
                clinical_context="Chronic hypertension history; may have vascular tortuosity.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Dilated Cardiomyopathy / Congestive Heart Failure",
                likelihood_category="High Prevalence",
                pathophysiology="Multichamber dilation and impaired systolic ejection fraction.",
                clinical_context="Exertional dyspnea, orthopnea, peripheral edema, elevated jugular venous pressure.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Pericardial Effusion",
                likelihood_category="Differential Consideration",
                pathophysiology="Accumulation of fluid in the pericardial sac producing a 'water-bottle' globular cardiac silhouette.",
                clinical_context="Distant heart sounds, electrical alternans; rapid accumulation leads to cardiac tamponade.",
                benign_vs_malignant="Benign",
            ),
        ],
        "uncertainty_statement": (
            "Cardiomegaly on a chest radiograph is a shadow measurement (>50% CTR on PA projection). Anteroposterior (AP) views, "
            "poor inspiratory effort, pectus excavatum, or obesity artificially magnify the heart silhouette without true disease."
        ),
        "diagnostic_limitations": "Radiographs cannot quantify ejection fraction, assess valvular dysfunction, or differentiate chamber hypertrophy from pericardial effusion.",
        "evidence_basis": "American Heart Association (AHA) / ACC Heart Failure Guidelines.",
        "recommended_follow_up": "Transthoracic echocardiography (TTE) is the gold standard for definitive anatomical and functional ventricular assessment.",
    },
    "atelectasis": {
        "name": "Atelectasis",
        "size_definition": "Loss of pulmonary aeration resulting in parenchymal volume collapse.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Subsegmental / Platelike Hypoventilation Collapse",
                likelihood_category="Most Common Post-Operative / Bedbound Finding",
                pathophysiology="Shallow breathing, splinting, or diaphragmatic elevation leading to dependent alveolar collapse.",
                clinical_context="Seen post-operatively, after prolonged recumbency, or secondary to pleuritic pain.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Mucus Plugging / Resorptive Bronchial Occlusion",
                likelihood_category="Common Acute Finding",
                pathophysiology="Complete airway obstruction with subsequent resorption of trapped alveolar gas.",
                clinical_context="Asthma, COPD exacerbations, or mechanically ventilated patients.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Obstructing Endobronchial Neoplasm",
                likelihood_category="Differential Concern in Persistent Lobar Collapse",
                pathophysiology="Central intraluminal tumor obstructing lobar or segmental bronchus (Golden S-curve sign).",
                clinical_context="Persistent non-resolving lobar atelectasis in an older adult or smoker.",
                benign_vs_malignant="Malignant",
            ),
        ],
        "uncertainty_statement": "Platelike basilar atelectasis is benign and transient; however, persistent unresolving lobar collapse requires exclusion of central airway obstruction.",
        "diagnostic_limitations": "Volume loss can cause mediastinal shift that obscures adjacent pathology.",
        "evidence_basis": "Radiological Society of North America (RSNA) Thoracic Radiography Reference Guidelines.",
        "recommended_follow_up": "Incentive spirometry and clinical follow-up. Bronchoscopy or contrast CT indicated if collapse fails to re-expand or involves an entire lobe.",
    },
    "infiltration": {
        "name": "Infiltration",
        "size_definition": "Ill-defined, hazy opacification involving interstitium or peripheral alveolar units.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Atypical or Viral Bronchopneumonia",
                likelihood_category="High Likelihood",
                pathophysiology="Peribronchial inflammatory infiltrates and interstitial edema caused by viral or atypical bacterial agents.",
                clinical_context="Subacute prodrome, low-grade fevers, non-productive cough, bilateral interstitial markings.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Interstitial Pulmonary Edema",
                likelihood_category="Common Cardiovascular Finding",
                pathophysiology="Fluid transudation into interlobular septa and peribronchovascular interstitium (Kerley B lines).",
                clinical_context="Associated cardiomegaly, orthopnea, and bilateral basilar distribution.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Drug-Induced Pneumonitis / Hypersensitivity",
                likelihood_category="Differential Consideration",
                pathophysiology="Immune-mediated lymphohistiocytic interstitial lung inflammation.",
                clinical_context="Temporal correlation with chemotherapy, immunotherapy (checkpoint inhibitors), or environmental antigens.",
                benign_vs_malignant="Benign",
            ),
        ],
        "uncertainty_statement": "'Infiltration' is a non-specific descriptive term. It encompasses infectious, inflammatory, edematous, and interstitial etiologies.",
        "diagnostic_limitations": "High inter-observer variability exists among radiologists regarding the label 'infiltration'.",
        "evidence_basis": "Fleischner Society Glossary of Terms for Thoracic Imaging.",
        "recommended_follow_up": "Clinical correlation with exposure history, medication review, and High-Resolution Chest CT (HRCT) if chronic or worsening.",
    },
    "pneumonia": {
        "name": "Pneumonia",
        "size_definition": "Infectious parenchymal consolidation or bronchopneumonic airspace filling.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Bacterial Community-Acquired Pneumonia (CAP)",
                likelihood_category="Primary Consideration",
                pathophysiology="Pyogenic alveolar exudation typically caused by Streptococcus pneumoniae, Haemophilus, or Moraxella.",
                clinical_context="Acute high fever, rigors, purulent sputum, localized crackles, bronchial breath sounds.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Aspiration Pneumonitis / Pneumonia",
                likelihood_category="Context Dependent",
                pathophysiology="Chemical or bacterial inflammation following aspiration of gastric contents or oropharyngeal secretions.",
                clinical_context="Dependent segments (superior lower lobes, posterior upper lobes); altered mentation or dysphagia.",
                benign_vs_malignant="Benign",
            ),
            ConditionInterpretationItem(
                condition_name="Post-Obstructive Pneumonia",
                likelihood_category="Differential Concern in Slow-Clearing Infiltrates",
                pathophysiology="Secondary infection developing distal to an intraluminal bronchial obstruction or neoplasm.",
                clinical_context="Recurrent pneumonia in the exact same anatomic lobe in a patient with cancer risk factors.",
                benign_vs_malignant="Malignant",
            ),
        ],
        "uncertainty_statement": "Radiographic pneumonia requires clinical correlation with patient symptoms, auscultation, and laboratory biomarkers; opacities lag clinical response by 4-8 weeks.",
        "diagnostic_limitations": "Early dehydration or profound neutropenia can cause false-negative radiographs during the first 24-48 hours.",
        "evidence_basis": "ATS/IDSA Guidelines on the Management of Community-Acquired Pneumonia.",
        "recommended_follow_up": "Empiric antimicrobial therapy per clinical severity scoring (CURB-65 / PSI). Follow-up radiograph in 6-8 weeks to confirm clearance in patients >50 years old.",
    },
    "no_finding": {
        "name": "No Finding",
        "size_definition": "Absence of gross targeted radiological findings above baseline thresholds.",
        "possible_conditions": [
            ConditionInterpretationItem(
                condition_name="Unremarkable Gross Thoracic Architecture",
                likelihood_category="Consistent with Image Appearance",
                pathophysiology="No gross consolidation, pneumothorax, effusion, or cardiomegaly visible on current projection.",
                clinical_context="Reassuring for acute gross thoracic emergencies on standard screening.",
                benign_vs_malignant="Non-Neoplastic / Baseline",
            ),
            ConditionInterpretationItem(
                condition_name="Radiographically Occult or Sub-Centimeter Pathology",
                likelihood_category="Cannot Be Excluded",
                pathophysiology="Early neoplasia, ground-glass nodules, non-calcified micro-metastases, or central endobronchial lesions.",
                clinical_context="A normal chest X-ray does NOT rule out lung cancer or early disease.",
                benign_vs_malignant="Cannot Rule Out",
            ),
        ],
        "uncertainty_statement": (
            "A 'No Finding' result indicates that the deep learning model did not detect gross targeted patterns "
            "exceeding current operating thresholds. IT DOES NOT CONSTITUTE A CLEAN BILL OF HEALTH OR CANCER-FREE PROOF. "
            "Chest radiography has documented low sensitivity (~60-70%) for small early-stage lung cancers."
        ),
        "diagnostic_limitations": "Cannot visualize retrocardiac, sub-diaphragmatic, apical, or hilum-obscured lesions < 1.0 cm.",
        "evidence_basis": "National Lung Screening Trial (NLST) findings on the limitations of standard radiography vs. LDCT.",
        "recommended_follow_up": "If clinical symptoms (hemoptysis, unexplained weight loss, persistent cough) or high risk (heavy smoking history) persist, referral for Low-Dose Chest CT (LDCT) is warranted.",
    },
}


class InterpretationService:
    """
    Decoupled clinical interpretation service for mapping model finding outputs
    to medically rigorous differentials, uncertainty disclosures, and follow-up guidance.
    """

    def interpret_findings(
        self,
        predictions: list[Any],
    ) -> ClinicalInterpretationResponse:
        """
        Take model predictions and construct a medically cautious, evidence-based interpretation.
        """
        finding_interpretations: list[FindingInterpretation] = []
        detected_names: list[str] = []
        secondary_names: list[str] = []

        for p in predictions:
            # Handle both dict and Pydantic object
            cond_id = getattr(p, "id", None) or p.get("id")
            name = getattr(p, "name", None) or p.get("name")
            prob = float(getattr(p, "probability", None) if getattr(p, "probability", None) is not None else p.get("probability", 0.0))
            thresh = float(getattr(p, "threshold", None) if getattr(p, "threshold", None) is not None else p.get("threshold", 0.40))
            detected = bool(getattr(p, "detected", None) if getattr(p, "detected", None) is not None else p.get("detected", False))
            severity = getattr(p, "severity", None) or p.get("severity", "low")

            kb_entry = FINDING_KNOWLEDGE_BASE.get(cond_id)
            if not kb_entry:
                continue

            # Populate interpretation for each finding
            item = FindingInterpretation(
                finding_id=cond_id,
                finding_name=name,
                probability=round(prob, 3),
                threshold=round(thresh, 3),
                detected=detected,
                severity=severity,
                size_definition=kb_entry.get("size_definition", ""),
                possible_conditions=kb_entry.get("possible_conditions", []),
                uncertainty_statement=kb_entry.get("uncertainty_statement", ""),
                diagnostic_limitations=kb_entry.get("diagnostic_limitations", ""),
                evidence_basis=kb_entry.get("evidence_basis", ""),
                recommended_follow_up=kb_entry.get("recommended_follow_up", ""),
            )
            finding_interpretations.append(item)

            if detected and cond_id not in ("no_finding", "normal"):
                detected_names.append(name)
            elif not detected and prob >= (thresh * 0.7) and cond_id not in ("no_finding", "normal"):
                secondary_names.append(name)

        # Build overall summary
        summary = OverallInterpretationSummary(
            primary_findings=detected_names,
            secondary_findings=secondary_names,
            has_detected_pathology=len(detected_names) > 0,
            negative_findings_disclaimer=(
                "Negative or sub-threshold model activations do not establish absence of disease or normal anatomy. "
                "Standard chest radiographs have documented physical sensitivity limits; early malignancies, micro-nodules, "
                "and non-targeted pathologies are frequently radiographically occult."
            ),
            oncologic_disclaimer=(
                "CRITICAL RESEARCH NOTICE: CXR-Explain outputs morphological finding probabilities only. "
                "The system CANNOT diagnose cancer, histological grade, or malignancy. A 'Mass' or 'Nodule' finding "
                "encompasses benign granulomas, hamartomas, infections, and neoplasms alike. Low scores do not rule out "
                "malignancy, high scores do not confirm cancer, and 'No Finding' does not establish absence of disease. "
                "Definitive diagnosis requires tissue biopsy, high-resolution CT, and comprehensive clinical evaluation."
            ),
            localization_disclaimer=(
                "LOCALIZATION NOTICE: Saliency heatmaps provided in CXR-Explain are generated via Grad-CAM (gradient-weighted "
                "class activation mapping) from DenseNet-121 layer denseblock4.denselayer16.conv2. This reflects neural feature "
                "attribution (gradient flow), NOT confirmed lesion boundaries, bounding boxes, or tissue segmentation. "
                "Faint raw activations are attenuated to prevent visual over-interpretation."
            ),
        )

        return ClinicalInterpretationResponse(
            summary=summary,
            findings=finding_interpretations,
        )


# Global singleton instance
interpretation_service = InterpretationService()

