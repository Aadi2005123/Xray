import type { SampleCxrCase } from '../types';

export const SAMPLE_CXR_CASES: SampleCxrCase[] = [
  {
    id: 'case_verified_clean',
    title: 'PA Chest: Clean Frontal Radiograph (Sample 01)',
    category: 'Pneumonia',
    summary: 'Genuine pristine frontal chest radiograph with bilateral lung fields, completely free of lead markers, arrows, colored outlines, or annotations.',
    thumbnailSvg: '/samples/sample_xray_clean.png',
    fullDataUrl: '/samples/sample_xray_clean.png',
    expectedPrimaryFinding: 'Research Sample (Unverified Cancer/Pathology Truth)',
  },
  {
    id: 'case_verified_nih',
    title: 'PA Chest: NIH Reference Scan (Sample 02)',
    category: 'Cardiomegaly',
    summary: 'Standard frontal radiograph from NIH ChestX-ray14 benchmark dataset (Patient 00000001; report text-mined finding: Cardiomegaly).',
    thumbnailSvg: '/samples/sample_xray.png',
    fullDataUrl: '/samples/sample_xray.png',
    expectedPrimaryFinding: 'Report Finding: Cardiomegaly (Unverified for Cancer)',
  },
  {
    id: 'case_standard_224',
    title: 'PA Chest: Frontal Test Asset (Sample 03)',
    category: 'Normal',
    summary: 'Standard 224x224 grayscale test asset for input validation and system testing; not clinical ground truth.',
    thumbnailSvg: '/samples/dummy_xray.png',
    fullDataUrl: '/samples/dummy_xray.png',
    expectedPrimaryFinding: 'Synthetic Validation Asset (Non-Clinical)',
  },
];
