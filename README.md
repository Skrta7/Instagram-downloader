# Instagram Video Downloader Bot

A Telegram bot that allows users to download Instagram videos, reels, and stories without the need to log in to an Instagram account. The bot includes an admin interface for managing user access and sending broadcasts.

## Features

- **Download Videos**: Easily download videos from Instagram by providing the post link.
- **User Management**: Admins can add or remove users from the admin list and ban/unban users.
- **Broadcast Messages**: Send announcements to all active users.
- **Logs Actions**: Keeps track of all actions performed by admins for transparency.

## Technologies Used

- Python
- Python-telegram-bot
- SQLite (for database management)

## Setup Instructions

1. **Clone the Repository**:
```
   git clone https://github.com/Good-Wizard/Instagram-downloader.git
   cd instagram-video-downloader-bot
```
## Usage
Start the Bot: Send /start to initiate the interaction with the bot.
### Admin Commands:
/addadmin <user_id>: Add a user as an admin.
/removeadmin <user_id>: Remove a user from the admin list.
/ban <user_id>: Ban a user from using the bot.
/unban <user_id>: Unban a previously banned user.
/broadcast <message>: Send a message to all users.
/send <user_id> <message>: Send a direct message to a specific user.
/admins: List all current admins.
## Contributing
#### If you'd like to contribute to this project, please fork the repository and create a pull request.

## Acknowledgements
Thanks to the Telegram and Instagram communities for providing excellent resources and support.

### Notes
1. **Customize Links and Tokens**: Make sure to replace placeholder links, such as the repository URL, with the actual links related to your project.
2. **Installation and Setup**: You might want to add more specific setup instructions, especially if there are unique configurations or environment variables required.
3. **Usage Examples**: You could add more examples of how users can interact with the bot.
