
import type {
  AnalysisProgressState,
  AnalysisResult,
  HeatmapData,
  ModelMetadata,
  ReportExportData,
  ClinicalInterpretationResponse,
} from '../types';

// Configure the backend URL through the Vite environment variable.
// Production Render default: https://xray-6ocw.onrender.com/api
// Local dev fallback: /api (proxied by Vite)
const API_BASE = (
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD
    ? 'https://xray-6ocw.onrender.com/api'
    : '/api')
).replace(/\/+$/, '');

const REQUEST_TIMEOUT_MS = 60000;

export interface HealthResponse {
  status: string;
  version: string;
  device: string;
  modelLoaded: boolean;
}

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs = REQUEST_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();

  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } catch (error: unknown) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(
        'Request timed out. The backend server may be waking up from cold start (Render free tier). Please retry in a moment.'
      );
    }

    if (error instanceof TypeError) {
      throw new Error(
        'Unable to connect to the backend server. Check network connectivity, CORS settings, or verify that the backend is online.'
      );
    }

    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function getErrorMessage(
  response: Response,
  fallback: string
): Promise<string> {
  try {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      const data: unknown = await response.json();
      if (typeof data === 'object' && data !== null) {
        const body = data as {
          detail?: unknown;
          message?: unknown;
          error?: unknown;
        };

        if (typeof body.detail === 'string') {
          return body.detail;
        }

        if (typeof body.message === 'string') {
          return body.message;
        }

        if (typeof body.error === 'string') {
          return body.error;
        }
      }
    } else {
      const text = await response.text();
      if (text && text.trim().length > 0 && text.length < 250) {
        return text.trim();
      }
    }
  } catch {
    // Fall back to HTTP status
  }

  return `${fallback} (HTTP ${response.status})`;
}

export const analysisApi = {
  // Check backend health.
  async checkHealth(): Promise<HealthResponse> {
    const response = await fetchWithTimeout(
      `${API_BASE}/health`,
      { method: 'GET' },
      10000
    );

    if (!response.ok) {
      throw new Error(
        await getErrorMessage(
          response,
          'Backend health check failed'
        )
      );
    }

    return (await response.json()) as HealthResponse;
  },

  // Retrieve model metadata.
  async getModelInfo(): Promise<ModelMetadata> {
    const response = await fetchWithTimeout(
      `${API_BASE}/model-info`,
      { method: 'GET' },
      15000
    );

    if (!response.ok) {
      throw new Error(
        await getErrorMessage(
          response,
          'Could not load model information'
        )
      );
    }

    return (await response.json()) as ModelMetadata;
  },

  // Upload and analyze an X-ray image.
  async analyzeXray(
    file: File | Blob,
    fileName: string,
    onProgress?: (progress: AnalysisProgressState) => void
  ): Promise<AnalysisResult> {
    onProgress?.({
      step: 'validating',
      percentage: 15,
      message: 'Validating the uploaded radiograph...',
    });

    const formData = new FormData();
    formData.append('file', file, fileName);

    onProgress?.({
      step: 'preprocessing',
      percentage: 40,
      message: 'Sending the image to the analysis backend...',
    });

    onProgress?.({
      step: 'inferring',
      percentage: 70,
      message: 'Waiting for the backend analysis result...',
    });

    const response = await fetchWithTimeout(
      `${API_BASE}/analyze`,
      {
        method: 'POST',
        body: formData,
      },
      REQUEST_TIMEOUT_MS
    );

    if (!response.ok) {
      throw new Error(
        await getErrorMessage(response, 'X-ray analysis failed')
      );
    }

    const result = (await response.json()) as AnalysisResult;

    onProgress?.({
      step: 'gradcam',
      percentage: 90,
      message: 'Preparing explanation data...',
    });

    onProgress?.({
      step: 'finalizing',
      percentage: 100,
      message: 'Analysis response received successfully.',
    });

    return result;
  },

  // Request a Grad-CAM explanation.
  async getGradCamExplanation(
    analysisId: string,
    conditionId: string
  ): Promise<HeatmapData> {
    const response = await fetchWithTimeout(
      `${API_BASE}/explain`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysisId,
          conditionId,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        await getErrorMessage(
          response,
          `Failed to generate explanation for ${conditionId}`
        )
      );
    }

    return (await response.json()) as HeatmapData;
  },

  // Request finding-based clinical interpretation.
  async getFindingInterpretation(
    analysisId: string
  ): Promise<ClinicalInterpretationResponse> {
    const response = await fetchWithTimeout(
      `${API_BASE}/interpret`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ analysisId }),
      }
    );

    if (!response.ok) {
      throw new Error(
        await getErrorMessage(
          response,
          'Failed to fetch clinical interpretation'
        )
      );
    }

    return (await response.json()) as ClinicalInterpretationResponse;
  },

  // Generate a report.
  async exportReport(
    data: ReportExportData
  ): Promise<{ reportUrl?: string; success: boolean }> {
    const response = await fetchWithTimeout(
      `${API_BASE}/report`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(
        await getErrorMessage(
          response,
          'Report generation failed'
        )
      );
    }

    return (await response.json()) as {
      reportUrl?: string;
      success: boolean;
    };
  },
};
