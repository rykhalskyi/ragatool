import { ExtensionCommand } from "./extensionCommand.js";

// Define InsertContentCommand class extending ExtensionCommand
class GetAccountListCommand extends ExtensionCommand {
    constructor() {
        super(
            "account_list",
            "Gets list of all accounts",
            `{}`,
            "Mozilla Thunderbird",
            ""
        );
    }

    async do(commandArg) {
        try {
            let accounts = (await messenger.accounts.list()).map(account => ({ id: account.id, name: account.name }));
            return { success: true, message: accounts };
        } catch (error) {
            console.error("Error inserting content:", error);
            return { success: false, message: error.message };
        }
    }
}

const emailQueryInputSchema = {
    "description": "Query for emails in Thunderbird. All properties are optional. See Thunderbird's messenger.messages.query documentation for all options.",
    "type": "object",
    "properties": {
        "subject": { "type": "string", "description": "Text contained in the message's subject." },
        "author": { "type": "string", "description": "Sender's name or email. e.g., 'John Doe <john.doe@example.com>'" },
        "recipients": { "type": "string", "description": "Recipient's name or email. For multiple, use a semicolon-separated list." },
        "fullText": { "type": "string", "description": "Text to search in the subject, body, or author." },
        "unread": { "type": "boolean", "description": "Set to true for unread messages, false for read." },
        "flagged": { "type": "boolean", "description": "Set to true for flagged messages." },
        "fromDate": { "type": "string", "format": "date-time", "description": "Return messages dated after this value (ISO 8601 format)." },
        "toDate": { "type": "string", "format": "date-time", "description": "Return messages dated before this value (ISO 8601 format)." },
        "folderId": { "type": ["string", "array"], "items": { "type": "string" }, "description": "ID of a folder (or array of IDs) to search in. Use 'list_folders' to get folder IDs." },
        "accountId": { "type": ["string", "array"], "items": { "type": "string" }, "description": "ID of an account (or array of IDs) to search in. Use 'account_list' to get account IDs." }
    }
};

class EmailQueryCommand extends ExtensionCommand {
    constructor() {
        super(
            "email_query",
            "Performs a detailed search for messages. Filter by subject, author, date, read status, etc. See input schema for all options.",
            JSON.stringify(emailQueryInputSchema, null, 2),
            "Mozilla Thunderbird",
            ""
        );
    }

    async do(commandArg) {
        try {
            console.log('query args:', commandArg);
            const queryInfo = typeof commandArg === 'string' ? JSON.parse(commandArg) : commandArg;
            let messages = await messenger.messages.query(queryInfo);
            return { success: true, message: messages };
        } catch (error) {
            console.error("Error in email_query:", error);
            return { success: false, message: error.message };
        }
    }
}

const getFullMessagesInputSchema = {
    "description": "Returns the specified message, including all headers and MIME parts. Requires a messageId and optionally accepts decoding options.",
    "type": "object",
    "properties": {
        "messageId": {
            "type": "integer",
            "description": "The unique integer ID representing a MessageHeader and the associated message. This is an internal tracking number that does not remain after a restart, nor does it follow an email that has been moved to a different folder."
        },
        "options": {
            "type": "object",
            "description": "Optional settings for decoding content, headers, and decryption.",
            "properties": {
                "decodeContent": { "type": "boolean", "description": "Whether to decode quoted-printable or base64 encoded content. Defaults to true." },
                "decodeHeaders": { "type": "boolean", "description": "Whether to decode RFC 2047 encoded headers. Defaults to true." },
                "decrypt": { "type": "boolean", "description": "Whether the message should be decrypted. Defaults to true." }
            }
        }
    },
    "required": ["messageId"]
};

class GetFullMessage extends ExtensionCommand {
    constructor() {
        super(
            "get_full_message",
            "Returns the specified message, including all headers and MIME parts. Throws if the message could not be read, for example due to network issues.",
            JSON.stringify(getFullMessagesInputSchema, null, 2),
            "Mozilla Thunderbird",
            ""
        );
    }

    async do(commandArg) {
        try {
            console.log('get_full_message args:', commandArg);
            const parsedArgs = typeof commandArg === 'string' ? JSON.parse(commandArg) : commandArg;
            const { messageId, options } = parsedArgs;
            if (!messageId) {
                throw new Error("messageId is required for GetFullMessagesCommand.");
            }
            let message = await messenger.messages.getFull(messageId, options);
            return { success: true, message: message };
        } catch (error) {
            console.error("Error in get_full_message:", error);
            return { success: false, message: error.message };
        }
    }
}


// Create instances of the commands
const getAccountListCommand = new GetAccountListCommand();
const emailQueryCommand = new EmailQueryCommand();
const getFullMessagesCommand = new GetFullMessage();


// Make a list and add these commands
const commands = [getAccountListCommand, emailQueryCommand, getFullMessagesCommand];

export function get_commands(entityName){
    for (const item of commands)
    {
        item.entityName = entityName;
        item.app = "Mozilla Thunderbird";
    }

    return commands;
}

export function find_command(commandName)
{
    return commands.find(cmd => cmd.name === commandName);
}