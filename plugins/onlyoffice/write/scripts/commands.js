import { ExtensionCommand } from './extensionCommand.js';
import { Editor } from './ragatouille.js';

// Define InsertContentCommand class extending ExtensionCommand
class InsertContentCommand extends ExtensionCommand {
    constructor() {
        super(
            "insert_content",
            "Insert HTML into document",
            `{ "content" : "string", "position" : "200" }`,
            "OnlyOffice DocX Editor",
            ""
        );
    }

    async do(commandArg) {
        try {
            const { content, position } = commandArg;
            await Editor.callCommand(function() {
                const oDocument = Api.GetDocument();
                const oParagraph = Api.CreateParagraph();
                oParagraph.AddText(content);
                oDocument.InsertContent([oParagraph]);
            });
            return { success: true, message: "Content inserted successfully" };
        } catch (error) {
            console.error("Error inserting content:", error);
            return { success: false, message: error.message };
        }
    }
}

// Define GetContentCommand class extending ExtensionCommand
class GetContentCommand extends ExtensionCommand {
    constructor() {
        super(
            "get_content",
            "Get content from the document in HTML",
            `{}`,
            "OnlyOffice DocX Editor",
            ""
        );
    }

    async do(commandArg) {
        try {
            const content = await Editor.callMethod("GetFileHTML");
            return { success: true, content: content };
        } catch (error) {
            console.error("Error getting content:", error);
            return { success: false, message: error.message };
        }
    }
}

// Create instances of the commands
const insertContentCmd = new InsertContentCommand();
const getContentCmd = new GetContentCommand();

// Make a list and add these commands
const commands = [insertContentCmd, getContentCmd];

export function get_commands(entityName){
    for (const item of commands)
    {
        item.entityName = entityName;
        item.app = "OnlyOffice Docx Editor (Word)"
    }

    return commands;
}

export function find_command(commandName)
{
    return commands.find(cmd => cmd.name === commandName);
}