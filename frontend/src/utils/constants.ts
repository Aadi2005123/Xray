export const MANDATORY_MEDICAL_DISCLAIMER =
  'AI-assisted screening/research prototype. Not a substitute for professional medical diagnosis.';

export const SECONDARY_ETHICAL_NOTICE =
  'All probabilities and visual saliency maps are calculated using deep learning representations and must be verified by a qualified radiologist or physician. Do not base acute patient management decisions solely on this automated output.';

export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

export const ACCEPTED_IMAGE_TYPES = [
  'image/png',
  'image/jpeg',
  'image/jpg',
  'image/webp',
];

export const THORACIC_CONDITIONS = [
  {
    id: 'atelectasis',
    name: 'Atelectasis',
    anatomicalRegion: 'Subsegmental / Lobar Lung Bases',
    description: 'Volume loss and collapse of alveolar units seen as linear or wedge-shaped opacities with fissure displacement.',
    clinicalSignificance: 'Frequently seen post-operatively, secondary to hypoventilation, mucus plugging, or airway obstruction.',
    defaultThreshold: 0.38,
  },
  {
    id: 'cardiomegaly',
    name: 'Cardiomegaly',
    anatomicalRegion: 'Cardiac Silhouette / Mediastinum',
    description: 'Enlargement of the cardiac silhouette exceeding 50% of the maximum thoracic diameter on PA projection.',
    clinicalSignificance: 'Associated with heart failure, cardiomyopathy, pericardial effusion, or valvular disease.',
    defaultThreshold: 0.45,
  },
  {
    id: 'consolidation',
    name: 'Consolidation',
    anatomicalRegion: 'Pulmonary Alveoli',
    description: 'Homogeneous opacification obscuring pulmonary vascular margins, typically with patent air-filled bronchi.',
    clinicalSignificance: 'Indicates replacement of alveolar air with fluid, blood, pus, or neoplastic cells.',
    defaultThreshold: 0.40,
  },
  {
    id: 'infiltration',
    name: 'Infiltration',
    anatomicalRegion: 'Interstitium / Airspaces',
    description: 'Abnormal opacification representing fluid, cellular exudate, or fibrosis within the lung parenchyma.',
    clinicalSignificance: 'Broad differential diagnosis including non-specific inflammatory, edema, or atypical infectious processes.',
    defaultThreshold: 0.35,
  },
  {
    id: 'mass',
    name: 'Mass',
    anatomicalRegion: 'Pulmonary Fields / Mediastinum',
    description: 'Circumscribed pulmonary or mediastinal lesion greater than 3 cm in diameter.',
    clinicalSignificance: 'Radiographic morphologic finding, not confirmed malignancy. Benign etiologies (granulomas, hamartomas, organizing pneumonia) present identically; tissue biopsy and CT are required for definitive histological diagnosis.',
    defaultThreshold: 0.35,
  },
  {
    id: 'nodule',
    name: 'Nodule',
    anatomicalRegion: 'Pulmonary Fields',
    description: 'Discrete rounded opacity less than 3 cm in diameter surrounded by aerated lung parenchyma.',
    clinicalSignificance: 'Solitary or multiple pulmonary nodules warranting Fleischner Society surveillance criteria. A low score does not rule out lung cancer, and a high score does not confirm malignancy.',
    defaultThreshold: 0.35,
  },
  {
    id: 'pneumonia',
    name: 'Pneumonia',
    anatomicalRegion: 'Pulmonary Parenchyma (Lobes)',
    description: 'Inflammatory consolidation or alveolar infiltrates within pulmonary airspace, often with air bronchograms.',
    clinicalSignificance: 'Acute infectious etiology requiring clinical correlation with vitals, auscultation, and biomarkers.',
    defaultThreshold: 0.40,
  },
  {
    id: 'pneumothorax',
    name: 'Pneumothorax',
    anatomicalRegion: 'Pleural Margin / Apex',
    description: 'Presence of gas within the pleural cavity with a visible visceral pleural line and absent peripheral lung markings.',
    clinicalSignificance: 'Critical acute finding; tension physiology mandates immediate clinical decompression.',
    defaultThreshold: 0.30,
  },
  {
    id: 'pleural_effusion',
    name: 'Pleural Effusion',
    anatomicalRegion: 'Costophrenic Angles / Pleural Space',
    description: 'Blunting of the lateral or posterior costophrenic sulci due to fluid accumulation in the pleural cavity.',
    clinicalSignificance: 'Indicative of transudative or exudative fluid collections (e.g., CHF, infection, malignancy).',
    defaultThreshold: 0.35,
  },
  {
    id: 'no_finding',
    name: 'No Finding',
    anatomicalRegion: 'Entire Thoracic Cavity',
    description: 'Absence of primary targeted radiographic features; clear lung fields and normal cardiothoracic ratio.',
    clinicalSignificance: 'Does not constitute proof of a normal radiograph or absence of cancer. Early malignancies, sub-centimeter nodules, central endobronchial lesions, or non-targeted pathologies cannot be excluded on radiograph alone.',
    defaultThreshold: 0.60,
  },
];
