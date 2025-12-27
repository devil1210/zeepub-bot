import { Skeleton } from "@/components/ui/skeleton"

export function CatalogSkeleton() {
    return (
        <div className="space-y-4">
            {/* Search Bar Skeleton (if on search page) */}
            <div className="flex gap-2 mb-6">
                <Skeleton className="h-12 flex-1 rounded-xl" />
                <Skeleton className="h-12 w-24 rounded-md" />
            </div>

            <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="flex gap-4 p-4 rounded-xl border border-border/50 bg-card/50">
                        {/* Folder/Book Cover Skeleton */}
                        <Skeleton className="w-16 h-24 rounded-lg flex-shrink-0" />

                        <div className="flex-1 space-y-2">
                            {/* Title */}
                            <Skeleton className="h-5 w-3/4 rounded" />
                            {/* Author */}
                            <Skeleton className="h-4 w-1/2 rounded" />
                            {/* Summary */}
                            <div className="space-y-1">
                                <Skeleton className="h-3 w-full rounded" />
                                <Skeleton className="h-3 w-2/3 rounded" />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
