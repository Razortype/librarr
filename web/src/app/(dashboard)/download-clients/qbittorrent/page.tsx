"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm, type Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CheckCircleIcon, XCircleIcon, Loader2Icon, Trash2Icon } from "lucide-react";
import { qbittorrentQueries, queryKeys } from "@/lib/queries";
import { integrationsApi } from "@/lib/api/integrations";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from "@/components/ui/form";
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import type { QBittorrentTestResult } from "@/lib/types";

// ── Schema ────────────────────────────────────────────────────────────────────

const formSchema = z.object({
  name: z.string().min(1, "Required").max(100),
  host: z.string().min(1, "Required"),
  port: z.coerce.number().int().min(1).max(65535),
  username: z.string().min(1, "Required"),
  password: z.string().min(1, "Required"),
  use_https: z.boolean(),
  enabled: z.boolean(),
});

type FormValues = z.infer<typeof formSchema>;

// ── Test result banner ────────────────────────────────────────────────────────

function TestResultBanner({ result }: { result: QBittorrentTestResult }) {
  if (result.ok) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400">
        <CheckCircleIcon className="size-4 shrink-0" />
        Connected to qBittorrent{result.version ? ` v${result.version}` : ""}
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
      <XCircleIcon className="size-4 shrink-0" />
      {result.error ?? "Connection failed"}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function QBittorrentConfigPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [testResult, setTestResult] = useState<QBittorrentTestResult | null>(null);

  const { data: existing, isLoading } = useQuery(qbittorrentQueries.config());

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema) as Resolver<FormValues>,
    defaultValues: {
      name: "",
      host: "",
      port: 8080,
      username: "",
      password: "",
      use_https: false,
      enabled: true,
    },
    values: existing
      ? {
          name: existing.name,
          host: existing.host,
          port: existing.port,
          username: existing.username,
          password: "",
          use_https: existing.use_https,
          enabled: existing.enabled,
        }
      : undefined,
  });

  const testMutation = useMutation({
    mutationFn: (vals: FormValues) =>
      integrationsApi.testQBittorrent({
        host: vals.host,
        port: vals.port,
        username: vals.username,
        password: vals.password,
        use_https: vals.use_https,
      }),
    onSuccess: (result) => setTestResult(result),
    onError: () =>
      setTestResult({ ok: false, version: null, error: "Request failed" }),
  });

  const saveMutation = useMutation({
    mutationFn: (vals: FormValues) => integrationsApi.upsertQBittorrent(vals),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.integrations.qbittorrent(),
      });
      router.push("/download-clients");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => integrationsApi.deleteQBittorrent(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.integrations.qbittorrent(),
      });
      router.push("/download-clients");
    },
  });

  const onTest = form.handleSubmit((vals) => {
    setTestResult(null);
    testMutation.mutate(vals);
  });

  const onSave = form.handleSubmit((vals) => {
    saveMutation.mutate(vals);
  });

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground text-sm">Loading…</p>
      </div>
    );
  }

  const isEdit = !!existing;

  return (
    <div className="p-6 max-w-xl">
      <div className="mb-6">
        <h2 className="text-base font-semibold">
          {isEdit ? "Edit qBittorrent" : "Add qBittorrent"}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Configure your qBittorrent download client.
        </p>
      </div>

      <Form {...form}>
        <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
          <Card>
            <CardHeader>
              <CardTitle>Connection</CardTitle>
              <CardDescription>Network settings for your qBittorrent instance.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Local qBittorrent" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-3 gap-3">
                <FormField
                  control={form.control}
                  name="host"
                  render={({ field }) => (
                    <FormItem className="col-span-2">
                      <FormLabel>Host</FormLabel>
                      <FormControl>
                        <Input placeholder="localhost" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="port"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Port</FormLabel>
                      <FormControl>
                        <Input type="number" placeholder="8080" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="use_https"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border border-border px-3 py-2.5">
                    <div>
                      <FormLabel>Use HTTPS</FormLabel>
                      <FormDescription>
                        Enable if qBittorrent is served over HTTPS.
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Authentication</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Username</FormLabel>
                    <FormControl>
                      <Input placeholder="admin" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="••••••••" {...field} />
                    </FormControl>
                    {isEdit && (
                      <FormDescription>
                        Password is not stored in plaintext. Re-enter to save changes.
                      </FormDescription>
                    )}
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <FormField
                control={form.control}
                name="enabled"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between">
                    <div>
                      <FormLabel>Enabled</FormLabel>
                      <FormDescription>
                        When disabled, librarr will not send downloads to this client.
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {testResult && <TestResultBanner result={testResult} />}

          {saveMutation.error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              Save failed:{" "}
              {saveMutation.error instanceof Error
                ? saveMutation.error.message
                : "Unknown error"}
            </div>
          )}

          <div className="flex items-center gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              disabled={testMutation.isPending}
              onClick={onTest}
            >
              {testMutation.isPending && (
                <Loader2Icon className="animate-spin" />
              )}
              Test Connection
            </Button>

            <Button
              type="button"
              disabled={saveMutation.isPending}
              onClick={onSave}
            >
              {saveMutation.isPending && (
                <Loader2Icon className="animate-spin" />
              )}
              Save
            </Button>

            <Button
              type="button"
              variant="ghost"
              onClick={() => router.push("/download-clients")}
            >
              Cancel
            </Button>

            {isEdit && (
              <div className="ml-auto">
                <AlertDialog>
                  <AlertDialogTrigger
                    render={
                      <Button
                        type="button"
                        variant="destructive"
                        disabled={deleteMutation.isPending}
                      />
                    }
                  >
                    {deleteMutation.isPending ? (
                      <Loader2Icon className="animate-spin" />
                    ) : (
                      <Trash2Icon />
                    )}
                    Delete
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Delete qBittorrent?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will remove the qBittorrent configuration. Active downloads
                        will not be affected.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        variant="destructive"
                        onClick={() => deleteMutation.mutate()}
                      >
                        Delete
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            )}
          </div>
        </form>
      </Form>
    </div>
  );
}
