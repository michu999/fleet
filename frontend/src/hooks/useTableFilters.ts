/**
 * Reusable hook for table filtering, searching, and sorting.
 * Works with any list of objects.
 *
 * Usage:
 *   const { search, setSearch, filtered } = useTableFilters(vehicles, {
 *     searchFields: ["plate_number", "brand", "model"],
 *     filters: [{ field: "status", value: hideInactive ? undefined : "inactive", exclude: true }],
 *   });
 */

import { useState, useMemo } from "react";

type Primitive = string | number | boolean | null | undefined;

interface FilterConfig<T> {
  /** Fields to search across (case-insensitive substring match) */
  searchFields?: (keyof T)[];
  /** Static field filters */
  filters?: {
    field: keyof T;
    value: Primitive;
    /** If true, exclude items where field === value */
    exclude?: boolean;
  }[];
}

interface UseTableFiltersResult<T> {
  search: string;
  setSearch: (value: string) => void;
  showInactive: boolean;
  setShowInactive: (value: boolean) => void;
  filtered: T[];
}

export function useTableFilters<T extends Record<string, Primitive>>(
  items: T[],
  config: FilterConfig<T> = {}
): UseTableFiltersResult<T> {
  const [search, setSearch] = useState("");
  const [showInactive, setShowInactive] = useState(false);

  const filtered = useMemo(() => {
    let result = items;

    // Hide inactive by default (looks for is_active or status fields)
    if (!showInactive) {
      result = result.filter((item) => {
        // Support boolean is_active field
        if ("is_active" in item) return item.is_active !== false;
        // Support status field with "inactive" value
        if ("status" in item) return item.status !== "inactive";
        return true;
      });
    }

    // Apply static filters
    if (config.filters) {
      for (const f of config.filters) {
        result = result.filter((item) => {
          if (f.exclude) return item[f.field] !== f.value;
          return item[f.field] === f.value;
        });
      }
    }

    // Apply search
    if (search.trim() && config.searchFields?.length) {
      const query = search.toLowerCase();
      result = result.filter((item) =>
        config.searchFields!.some((field) => {
          const val = item[field];
          return val != null && String(val).toLowerCase().includes(query);
        })
      );
    }

    return result;
  }, [items, search, showInactive, config.filters, config.searchFields]);

  return { search, setSearch, showInactive, setShowInactive, filtered };
}