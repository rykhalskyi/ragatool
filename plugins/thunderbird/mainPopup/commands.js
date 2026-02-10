import { ExtensionCommand } from "./extensionCommand.js";

// Define InsertContentCommand class extending ExtensionCommand
class HealthCheckCommand extends ExtensionCommand {
    constructor() {
        super(
            "health_check",
            "Echoes the input string",
            `{ "content" : "string" }`,
            "Mozilla Thunderbird",
            ""
        );
    }

    async do(commandArg) {
        try {
            const { content } = commandArg;
            console.log('Health check', content);
            return { success: true, message: content };
        } catch (error) {
            console.error("Error inserting content:", error);
            return { success: false, message: error.message };
        }
    }
}




// Create instances of the commands
const healthCheckCommand = new HealthCheckCommand();


// Make a list and add these commands
const commands = [healthCheckCommand];

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