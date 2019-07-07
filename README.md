# voice2textMatrix
Matrix bot convert voice messages to text over cloud api.

Use:
1. Invite this bot to your matrix-room.
2. If any user in this room send voice message - bot give this message,
3. Send to cloud (now yandex) for translate it to text
4. send result text as notify-message to this room.

Setup:
1. create bot matrix account as simple user account.
2. get yandex oauth-token at this link: 
yandex speach cloud API settings:
https://cloud.yandex.ru/docs/iam/operations/iam-token/create
3. set options at bot config: oauth="XXXXXX"
4. get folder id (from default) at yandex: https://console.cloud.yandex.ru/cloud 
May be you need create pay account for this by link: https://console.cloud.yandex.ru/
5. setup options at config: folder_id = "XXXXXX"
6. run bot.py
