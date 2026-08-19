# Twitch Access Token Scopes

Each API that your app calls, and EventSub subscription your application subscribes to, specifies the type of token it requires. For example, some APIs require a User Access Token and others require an App Access Token. For APIs that require a User Access Token, the API reference content identifies the scopes that the user must authorize. The authorization gives your app permission to perform the specified action on the user’s behalf. App access tokens don’t use scopes.

When you send an HTTP GET request to `https://id.twitch.tv/oauth2/authorize`, you set the *scope* query parameter to the list of scopes required to support your app’s functionality. The list is space delimited. You must URL encode the list; for example, `&scope=user%3Aedit%20user%3Aread%3Aemail`.

**NOTE** An application must request only the scopes required by the APIs that their app calls. If you request more scopes than is required to support your app’s functionality, Twitch may suspend your application’s access to the Twitch API.

## Twitch API and EventSub scopes

The following table lists the scopes used by the Twitch API. To see a list of all Twitch API endpoints, including those that do not require scopes, see the Twitch API reference.

| Scope Name | Type of Access and Associated Endpoints |
|---|---|
| `analytics:read:extensions` | View analytics data for the Twitch Extensions owned by the authenticated account.**API**Get Extension Analytics |
| `analytics:read:games` | View analytics data for the games owned by the authenticated account.**API**Get Game Analytics |
| `bits:read` | View Bits-related products and redemptions for a channel.**API**Get Bits LeaderboardGet Custom Power-up**EventSub**Channel Bits UseChannel CheerChannel Custom Power-ups Redemption Add |
| `channel:bot` | Joins your channel’s chatroom as a bot user, and perform chat-related actions as that user.**API**Send Chat Message**EventSub**Channel Chat ClearChannel Chat Clear User MessagesChannel Chat MessageChannel Chat Message DeleteChannel Chat NotificationChannel Chat Settings Update |
| `channel:manage:ads` | Manage ads schedule on a channel.**API**Snooze Next Ad |
| `channel:read:ads` | Read the ads schedule and details on your channel.**API**Get Ad Schedule**EventSub**Channel Ad Break Begin |
| `channel:manage:broadcast` | Manage a channel’s broadcast configuration, including updating channel configuration and managing stream markers and stream tags.**API**Modify Channel InformationCreate Stream MarkerReplace Stream Tags |
| `channel:read:charity` | Read charity campaign details and user donations on your channel.**API**Get Charity CampaignGet Charity Campaign Donations**EventSub**Charity DonationCharity Campaign StartCharity Campaign ProgressCharity Campaign Stop |
| `channel:manage:clips` | Manage Clips for a channel.**API**Create Clip From VODGet Clips Download |
| `channel:edit:commercial` | Run commercials on a channel.**API**Start Commercial |
| `channel:read:editors` | View a list of users with the editor role for a channel.**API**Get Channel Editors |
| `channel:manage:extensions` | Manage a channel’s Extension configuration, including activating Extensions.**API**Get User Active ExtensionsUpdate User Extensions |
| `channel:read:goals` | View Creator Goals for a channel.**API**Get Creator Goals**EventSub**Goal BeginGoal ProgressGoal End |
| `channel:read:guest_star` | Read Guest Star details for your channel.**API**Get Channel Guest Star SettingsGet Guest Star SessionGet Guest Star Invites**EventSub**Channel Guest Star Session BeginChannel Guest Star Session EndChannel Guest Star Guest UpdateChannel Guest Star Settings Update |
| `channel:manage:guest_star` | Manage Guest Star for your channel.**API**Update Channel Guest Star SettingsCreate Guest Star SessionEnd Guest Star SessionSend Guest Star InviteDelete Guest Star InviteAssign Guest Star SlotUpdate Guest Star SlotDelete Guest Star SlotUpdate Guest Star Slot Settings**EventSub**Channel Guest Star Session BeginChannel Guest Star Session EndChannel Guest Star Guest UpdateChannel Guest Star Settings Update |
| `channel:read:hype_train` | View Hype Train information for a channel.**API**Get Hype Train Status**EventSub**Hype Train BeginHype Train ProgressHype Train End |
| `channel:manage:moderators` | Add or remove the moderator role from users in your channel.**API**Add Channel ModeratorRemove Channel ModeratorGet Moderators |
| `channel:read:polls` | View a channel’s polls.**API**Get Polls**EventSub**Channel Poll BeginChannel Poll ProgressChannel Poll End |
| `channel:manage:polls` | Manage a channel’s polls.**API**Get PollsCreate PollEnd Poll**EventSub**Channel Poll BeginChannel Poll ProgressChannel Poll End |
| `channel:read:predictions` | View a channel’s Channel Points Predictions.**API**Get Channel Points Predictions**EventSub**Channel Prediction BeginChannel Prediction ProgressChannel Prediction LockChannel Prediction End |
| `channel:manage:predictions` | Manage of channel’s Channel Points Predictions**API**Get Channel Points PredictionsCreate Channel Points PredictionEnd Channel Points Prediction**EventSub**Channel Prediction BeginChannel Prediction ProgressChannel Prediction LockChannel Prediction End |
| `channel:manage:raids` | Manage a channel raiding another channel.**API**Start a raidCancel a raid |
| `channel:read:redemptions` | View Channel Points custom rewards and their redemptions on a channel.**API**Get Custom RewardGet Custom Reward Redemption**EventSub**Channel Points Automatic Reward RedemptionChannel Points Automatic Reward Redemption v2Channel Points Custom Reward AddChannel Points Custom Reward UpdateChannel Points Custom Reward RemoveChannel Points Custom Reward Redemption AddChannel Points Custom Reward Redemption Update |
| `channel:manage:redemptions` | Manage Channel Points custom rewards and their redemptions on a channel.**API**Get Custom RewardGet Custom Reward RedemptionCreate Custom RewardsDelete Custom RewardUpdate Custom RewardUpdate Redemption Status**EventSub**Channel Points Automatic Reward RedemptionChannel Points Custom Reward AddChannel Points Custom Reward UpdateChannel Points Custom Reward RemoveChannel Points Custom Reward Redemption AddChannel Points Custom Reward Redemption Update |
| `channel:manage:schedule` | Manage a channel’s stream schedule.**API**Update Channel Stream ScheduleCreate Channel Stream Schedule SegmentUpdate Channel Stream Schedule SegmentDelete Channel Stream Schedule Segment |
| `channel:read:stream_key` | View an authorized user’s stream key.**API**Get Stream Key |
| `channel:read:subscriptions` | View a list of all subscribers to a channel and check if a user is subscribed to a channel.**API**Get Broadcaster Subscriptions**EventSub**Channel SubscribeChannel Subscription EndChannel Subscription GiftChannel Subscription Message |
| `channel:manage:videos` | Manage a channel’s videos, including deleting videos.**API**Delete Videos |
| `channel:read:vips` | Read the list of VIPs in your channel.**API**Get VIPs**EventSub**Channel VIP AddChannel VIP Remove |
| `channel:manage:vips` | Add or remove the VIP role from users in your channel.**API**Get VIPsAdd Channel VIPRemove Channel VIP**EventSub**Channel VIP AddChannel VIP Remove |
| `channel:moderate` | Perform moderation actions in a channel.**EventSub**Channel BanChannel Unban |
| `clips:edit` | Manage Clips for a channel.**API**Create Clip |
| `editor:manage:clips` | Manage Clips as an editor.**API**Create Clip From VODGet Clips Download |
| `moderation:read` | View a channel’s moderation data including Moderators, Bans, Timeouts, and Automod settings.**API**Check AutoMod StatusGet Banned UsersGet Moderators**EventSub**Channel Moderator AddChannel Moderator Remove |
| `moderator:manage:announcements` | Send announcements in channels where you have the moderator role.**API**Send Chat Announcement |
| `moderator:manage:automod` | Manage messages held for review by AutoMod in channels where you are a moderator.**API**Manage Held AutoMod Messages**EventSub**AutoMod Message HoldAutoMod Message Hold v2AutoMod Message UpdateAutoMod Message Update v2AutoMod Terms Update |
| `moderator:read:automod_settings` | View a broadcaster’s AutoMod settings.**API**Get AutoMod Settings**EventSub**AutoMod Settings Update |
| `moderator:manage:automod_settings` | Manage a broadcaster’s AutoMod settings.**API**Update AutoMod Settings |
| `moderator:read:banned_users` | Read the list of bans or unbans in channels where you have the moderator role.**EventSub**Channel ModerateChannel Moderate v2 |
| `moderator:manage:banned_users` | Ban and unban users.**API**Get Banned UsersBan UserUnban User**EventSub**Channel ModerateChannel Moderate v2 |
| `moderator:read:blocked_terms` | View a broadcaster’s list of blocked terms.**API**Get Blocked Terms**EventSub**Channel Moderate |
| `moderator:manage:blocked_terms` | Manage a broadcaster’s list of blocked terms.**API**Get Blocked TermsAdd Blocked TermRemove Blocked Term**EventSub**Channel Moderate |
| `moderator:read:chat_messages` | Read deleted chat messages in channels where you have the moderator role and get pinned chat messages.**API**Get Pinned Chat Message**EventSub**Channel Moderate |
| `moderator:manage:chat_messages` | Delete chat messages in channels where you have the moderator role and manage pinned chat messages.**API**Delete Chat MessagesPin Chat MessageUpdate Pinned Chat MessageUnpin Chat Message**EventSub**Channel Moderate |
| `moderator:read:chat_settings` | View a broadcaster’s chat room settings.**API**Get Chat Settings**EventSub**Channel Moderate |
| `moderator:manage:chat_settings` | Manage a broadcaster’s chat room settings.**API**Update Chat Settings**EventSub**Channel Moderate |
| `moderator:read:chatters` | View the chatters in a broadcaster’s chat room.**API**Get Chatters |
| `moderator:read:followers` | Read the followers of a broadcaster.**API**Get Channel Followers**EventSub**Channel Follow |
| `moderator:read:guest_star` | Read Guest Star details for channels where you are a Guest Star moderator.**API**Get Channel Guest Star SettingsGet Guest Star SessionGet Guest Star Invites**EventSub**Channel Guest Star Session BeginChannel Guest Star Session EndChannel Guest Star Guest UpdateChannel Guest Star Settings Update |
| `moderator:manage:guest_star` | Manage Guest Star for channels where you are a Guest Star moderator.**API**Send Guest Star InviteDelete Guest Star InviteAssign Guest Star SlotUpdate Guest Star SlotDelete Guest Star SlotUpdate Guest Star Slot Settings**EventSub**Channel Guest Star Session BeginChannel Guest Star Session EndChannel Guest Star Guest UpdateChannel Guest Star Settings Update |
| `moderator:read:moderators` | Read the list of moderators in channels where you have the moderator role.**EventSub**Channel ModerateChannel Moderate v2 |
| `moderator:read:shield_mode` | View a broadcaster’s Shield Mode status.**API**Get Shield Mode Status**EventSub**Shield Mode BeginShield Mode End |
| `moderator:manage:shield_mode` | Manage a broadcaster’s Shield Mode status.**API**Update Shield Mode Status**EventSub**Shield Mode BeginShield Mode End |
| `moderator:read:shoutouts` | View a broadcaster’s shoutouts.**EventSub**Shoutout CreateShoutout Received |
| `moderator:manage:shoutouts` | Manage a broadcaster’s shoutouts.**API**Send a Shoutout**EventSub**Shoutout CreateShoutout Received |
| `moderator:read:suspicious_users` | Read chat messages from suspicious users and see users flagged as suspicious in channels where the user has the moderator role.**EventSub**Channel Suspicious User MessageChannel Suspicious User Update |
| `moderator:manage:suspicious_users` | Manage suspicious user statuses in channels where the user has the moderator role.**API**Add suspicious status to chat userRemove suspicious status from chat user |
| `moderator:read:unban_requests` | View a broadcaster’s unban requests.**API**Get Unban Requests**EventSub**Channel Unban Request CreateChannel Unban Request ResolveChannel Moderate |
| `moderator:manage:unban_requests` | Manage a broadcaster’s unban requests.**API**Resolve Unban Requests**EventSub**Channel Unban Request CreateChannel Unban Request ResolveChannel Moderate |
| `moderator:read:vips` | Read the list of VIPs in channels where you have the moderator role.**EventSub**Channel ModerateChannel Moderate v2 |
| `moderator:read:warnings` | Read warnings in channels where you have the moderator role.**EventSub**Channel Moderate v2Channel Warning AcknowledgeChannel Warning Send |
| `moderator:manage:warnings` | Warn users in channels where you have the moderator role.**API**Warn Chat User**EventSub**Channel Moderate v2Channel Warning AcknowledgeChannel Warning Send |
| `user:bot` | Join a specified chat channel as your user and appear as a bot, and perform chat-related actions as your user.**API**Send Chat Message**EventSub**Channel Chat ClearChannel Chat Clear User MessagesChannel Chat MessageChannel Chat Message DeleteChannel Chat NotificationChannel Chat Settings UpdateChannel Chat User Message HoldChannel Chat User Message Update |
| `user:edit` | Manage a user object.**API**Update User |
| `user:edit:broadcast` | View and edit a user’s broadcasting configuration, including Extension configurations.**API**Get User ExtensionsGet User Active ExtensionsUpdate User Extensions |
| `user:read:blocked_users` | View the block list of a user.**API**Get User Block List |
| `user:manage:blocked_users` | Manage the block list of a user.**API**Block UserUnblock User |
| `user:read:broadcast` | View a user’s broadcasting configuration, including Extension configurations.**API**Get Stream MarkersGet User ExtensionsGet User Active Extensions |
| `user:read:chat` | Receive chatroom messages and informational notifications relating to a channel’s chatroom.**EventSub**Channel Chat ClearChannel Chat Clear User MessagesChannel Chat MessageChannel Chat Message DeleteChannel Chat NotificationChannel Chat Settings UpdateChannel Chat User Message HoldChannel Chat User Message Update |
| `user:manage:chat_color` | Update the color used for the user’s name in chat.**API**Update User Chat Color |
| `user:read:email` | View a user’s email address.**API**Get Users (optional)Update User (optional)**EventSub**User Update (optional) |
| `user:read:emotes` | View emotes available to a user**API**Get User Emotes |
| `user:read:follows` | View the list of channels a user follows.**API**Get Followed ChannelsGet Followed Streams |
| `user:read:moderated_channels` | Read the list of channels you have moderator privileges in.**API**Get Moderated Channels |
| `user:read:subscriptions` | View if an authorized user is subscribed to specific channels.**API**Check User Subscription |
| `user:read:whispers` | Receive whispers sent to your user.**EventSub**Whisper Received |
| `user:manage:whispers` | Receive whispers sent to your user, and send whispers on your user’s behalf.**API**Send Whisper**EventSub**Whisper Received |
| `user:write:chat` | Send chat messages to a chatroom.**API**Send Chat Message |

## IRC Chat Scopes

The following table lists the scopes used by Twitch IRC.

| Scope Name | Type of Access |
|---|---|
| `chat:edit` | Send chat messages to a chatroom using an IRC connection. |
| `chat:read` | View chat messages sent in a chatroom using an IRC connection. |

## PubSub-specific Chat Scopes

The following table lists the scopes used only by PubSub. There may be additional scopes needed for some PubSub topics, but those are not listed here.

| Scope Name | Type of Access |
|---|---|
| `whispers:read` | Receive whisper messages for your user using PubSub. |