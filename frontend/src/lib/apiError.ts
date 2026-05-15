type ValidationErrorItem = {
  loc?: (string | number)[];
  msg?: string;
};

type ApiErrorBody = {
  detail?: string | ValidationErrorItem[];
};

function detailMessage(detail: ApiErrorBody["detail"]): string | null {
  if (!detail) {
    return null;
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = item.loc?.slice(-1)[0];
        const msg = item.msg ?? "Invalid value";
        return field ? `${field}: ${msg}` : msg;
      })
      .join("; ");
  }
  return null;
}

export function formatApiError(error: unknown, fallback: string): string {
  if (!error || typeof error !== "object") {
    return fallback;
  }

  const record = error as { body?: ApiErrorBody; detail?: ApiErrorBody["detail"] };
  const fromBody = detailMessage(record.body?.detail);
  if (fromBody) {
    return fromBody;
  }

  const fromRoot = detailMessage(record.detail);
  if (fromRoot) {
    return fromRoot;
  }

  return fallback;
}
