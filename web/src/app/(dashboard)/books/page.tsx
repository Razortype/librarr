import { Suspense } from "react";
import { BooksPageClient } from "@/components/books/books-page-client";

export default async function BooksPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  await searchParams;
  return (
    <Suspense fallback={null}>
      <BooksPageClient />
    </Suspense>
  );
}
