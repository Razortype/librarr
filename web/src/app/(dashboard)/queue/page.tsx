import { Suspense } from "react";
import { QueuePageClient } from "@/components/queue/queue-page-client";

export default async function QueuePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  await searchParams;
  return (
    <Suspense fallback={null}>
      <QueuePageClient />
    </Suspense>
  );
}
