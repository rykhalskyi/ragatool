// import { ExtensionCommand } from './extensionCommand.js';
const ExtensionCommand = window.ExtensionCommand;
// import { Editor } from './ragatouille.js';
const Editor = window.Editor;

const insertContentInputSchema = {
    "type": "object",
    "properties": {
        "content" : {
            "type" : "string",
            "description": "Text to be inserted"
        }
    }
}

// Define InsertContentCommand class extending ExtensionCommand
class InsertContentCommand extends ExtensionCommand {
    constructor() {
        super(
            "insert_content",
            "Insert HTML into document",
            JSON.stringify(insertContentInputSchema, null, 2),
            "OnlyOffice DocX Editor",
            ""
        );
    }

    async do(commandArg) {
        try {
            let arg = commandArg;
            if (typeof commandArg === "string")
            {
                arg = JSON.parse(arg);
            }

            const { content } = arg;
            console.log('text to insert', arg, content);

            const userCode = `
                const oDocument = Api.GetDocument();
                const oParagraph = Api.CreateParagraph();
                oParagraph.AddText('${content.replace(/'/g, "\\'")}');
                oDocument.InsertContent([oParagraph]);
            `;
            
            const func = new Function(userCode);
            await window.Editor.callCommand(func);

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
            return await window.Editor.callCommand(function() {
                const oDocument = Api.GetDocument();
                var allText = oDocument.GetText();
                return { success: true, content: allText };
            });
        } catch (error) {
            console.error("Error getting content:", error);
            return { success: false, message: error.message };
        }
    }
}

const runApiCodeInputSchema = {
    "type": "object",
    "properties": {
        "userCode" : {
            "type" : "string",
            "description": "Javascript code to run. Code should use office-js-api OnlyOffice API"
        }
    }
}

class RunApiCodeCommand extends ExtensionCommand{
    constructor(){
        super(
            "run_api_code",
            "Runs your office-js-api code in Only Office runtime container. container is:" +
                'try {' +
                '  const __result = (function() {' +
                '     + userCode + ' +
                '  })();' +
                '  return { success: true, result: __result === undefined ? null : __result };' +
                '} catch(e) {' +
                '  return { success: false, message: e && e.message ? e.message : String(e) };' +
                '}'+ 'Example of user code: return Api.GetFullName();',
             JSON.stringify(runApiCodeInputSchema, null, 2),
            "OnlyOffice DocX Editor",
            ""
        );
    }

    async do(commandArg) {
        try {

            if (typeof commandArg === "string") {
               commandArg = JSON.parse(commandArg);
            }

            const code = commandArg && commandArg.userCode;
            if (!code) {
                return { success: false, message: "No code provided" };
            }

            // Build a function that will run inside the editor context.
            // We serialize the user code as a string and eval it there, capturing result/errors.
            const func = new Function(
                'try {\n' +
                '  const __result = (function() {\n' +
                '    ' + code + '\n' +
                '  })();\n' +
                '  return { success: true, result: __result === undefined ? null : __result };\n' +
                '} catch(e) {\n' +
                '  return { success: false, message: e && e.message ? e.message : String(e) };\n' +
                '}'
            );

            console.log('RUN API CODE FUNC', func);
            const result = await window.Editor.callCommand(func);
            return result;
        } catch (error) {
            console.error("Error running code:", error);
            return { success: false, message: error && error.message ? error.message : String(error) };
        }
    }
}

const runCodeInputSchema = {
    "type": "object",
    "properties": {
        "userCode" : {
            "type" : "string",
            "description": "Javascript code to run. Code should use plugin-and-macros OnlyOffice API"
        }
    }
}

class RunCodeCommand extends ExtensionCommand{
        constructor(){
        super(
            "run_code",
            "Runs your code in Only Office runtime ouside office-api conatainer. This needs plugin-and-macros funcions"+
             "Example of user code:"+
                'let version = await window.Editor.callMethod("GetVersion");'+
                'await window.Editor.callMethod("PasteHtml", ["<span>Hello, </span><span><b>world</b></span><span>!</span>"]);'+
                'return verion;',
            JSON.stringify(runCodeInputSchema, null, 2),
            "OnlyOffice DocX Editor",
            ""
        );
    }

    async do(commandArg) {
        try {
            if (typeof commandArg === "string") {
               commandArg = JSON.parse(commandArg);
            }

            const code = commandArg && commandArg.userCode;
            if (!code) {
                return { success: false, message: "No code provided" };
            }

            const userFunction = new Function(
                'return (async function() {' +
                code +
                '})();'
            );
            const result = await userFunction();

            return { success: true, result: result === undefined ? null : result };

        } catch (error) {
            console.error("Error running user code:", error);
            return { success: false, message: error && error.message ? error.message : String(error) };
        }
    }
}


// Create instances of the commands
const insertContentCmd = new InsertContentCommand();
const getContentCmd = new GetContentCommand();
const runApiCodeCommand = new RunApiCodeCommand();
const runCodeCommand = new RunCodeCommand();

// Make a list and add these commands
const commands = [insertContentCmd, getContentCmd, runApiCodeCommand, runCodeCommand];

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