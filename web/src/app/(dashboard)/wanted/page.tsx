import { Suspense } from "react";
import { WantedPageClient } from "@/components/wanted/wanted-page-client";

export default async function WantedPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  await searchParams;
  return (
    <Suspense fallback={null}>
      <WantedPageClient />
    </Suspense>
  );
}
