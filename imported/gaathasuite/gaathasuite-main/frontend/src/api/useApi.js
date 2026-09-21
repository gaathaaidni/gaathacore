import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '../api/axiosInstance';

/**
 * Custom hook for authenticated GET requests using React Query
 */
export const useAuthQuery = (queryKey, endpoint, options = {}) => {
  return useQuery({
    queryKey,
    queryFn: () => axiosInstance.get(endpoint).then(res => res.data),
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
};

export const useAuthMutation = (mutationFn, options = {}) => {
  return useMutation({
    mutationFn,
    ...options,
  });
};