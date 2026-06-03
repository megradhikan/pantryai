// Runs daily at 8AM via Supabase cron (configure in Supabase dashboard)
// Sends Web Push to users with items expiring tomorrow

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import webpush from "npm:web-push";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
);

webpush.setVapidDetails(
  `mailto:${Deno.env.get("VAPID_EMAIL")}`,
  Deno.env.get("VAPID_PUBLIC_KEY")!,
  Deno.env.get("VAPID_PRIVATE_KEY")!
);

Deno.serve(async () => {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split("T")[0];

  const { data: items } = await supabase
    .from("inventory_items")
    .select("user_id, name")
    .eq("estimated_expiry", tomorrowStr)
    .eq("is_finished", false);

  const byUser: Record<string, string[]> = {};
  for (const item of items ?? []) {
    if (!byUser[item.user_id]) byUser[item.user_id] = [];
    byUser[item.user_id].push(item.name);
  }

  for (const [userId, itemNames] of Object.entries(byUser)) {
    const { data: subs } = await supabase
      .from("push_subscriptions")
      .select("endpoint, p256dh, auth")
      .eq("user_id", userId);

    const body =
      itemNames.length === 1
        ? `${itemNames[0]} expires tomorrow.`
        : `${itemNames.length} items expire tomorrow: ${itemNames.slice(0, 2).join(", ")}${itemNames.length > 2 ? "..." : ""}`;

    for (const sub of subs ?? []) {
      await webpush.sendNotification(
        { endpoint: sub.endpoint, keys: { p256dh: sub.p256dh, auth: sub.auth } },
        JSON.stringify({ title: "PantryAI", body })
      );
    }
  }

  return new Response("done");
});
