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
6. install boto3 by: pip install boto3
7. install pydub by: pip install pydub
8. install audio tools: apt-get install libav-tools libavcodec-extra
9. mkdir ~/.aws 
10. cp and edit: cp aws_credentials.example ~/.aws/credentials (get key from https://console.cloud.yandex.ru/cloud, enter catalog, enter service account, create access key , store key_id and key_secret to this config )
11. cp aws_config.example ~/.aws/config
12. create "auth key" (as 10.) and save private key as file key.pem. Set in config.py  service_secret_key_path="key.pem"
13. install jwt by: pip install PyJWT
14. run bot.py
