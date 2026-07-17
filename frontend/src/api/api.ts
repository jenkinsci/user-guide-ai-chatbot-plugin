interface ApiRequestParams {
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  payload?: object;
}

export const apiCall = async ({ method, path, payload }: ApiRequestParams) => {
  if (import.meta.env.PROD) {
    return proxyApiCall({
      method,
      path,

      payload,
    });
  } else {
    return devApiCall({
      method,
      path,
      payload,
    });
  }
};

export const devApiCall = async ({
  method,
  path,
  payload,
}: ApiRequestParams) => {
  const DUMMY_JWT_KEY = import.meta.env.VITE_DUMMY_JWT_KEY;
  const DEV_API_URL = import.meta.env.VITE_DEV_API_URL;
  const FINAL_PATH = DEV_API_URL + path;

  try {
    const response = await fetch(FINAL_PATH, {
      method: method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${DUMMY_JWT_KEY}`,
      },
      body:
        payload &&
        JSON.stringify({
          ...payload,
        }),
    });

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    return response;
  } catch (error) {
    console.error(`Failed to ${method} request to ${FINAL_PATH}:`, error);
    throw error;
  }
};

export const proxyApiCall = async ({
  method,
  path,
  payload,
}: ApiRequestParams) => {
  const rootElement = document.getElementById("jenkins-ai-chatbot-root");
  const proxyUrl = rootElement?.getAttribute("data-api-url") || "";
  const crumbHeader =
    rootElement?.getAttribute("data-crumb-header") || "Jenkins-Crumb";
  const crumbValue = rootElement?.getAttribute("data-crumb-value") || "";

  const fullUrl = proxyUrl + path;

  try {
    const response = await fetch(fullUrl, {
      method: method,
      headers: {
        "Content-Type": "application/json",
        [crumbHeader]: crumbValue,
      },
      body:
        payload &&
        JSON.stringify({
          ...payload,
        }),
    });

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    return response;
  } catch (error) {
    console.error(`Failed to proxy ${method} request to ${path}:`, error);
    throw error;
  }
};
