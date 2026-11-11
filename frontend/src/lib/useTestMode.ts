import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

/** True while the server runs in test mode (every wait zero). Shares the banner's query. */
export function useTestMode(): boolean {
  const features = useQuery({ queryKey: ["features"], queryFn: () => api.features(), staleTime: Infinity });
  return features.data?.test_mode === true;
}
