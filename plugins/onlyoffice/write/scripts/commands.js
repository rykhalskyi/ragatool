const commands = [
    new ExtensionCommand(
        "ask",
        "Ask a question to the model",
        `{ "question": "string" }`,
        "RAGatouille",
        "RAG"
    ),
    new ExtensionCommand(
        "get_context",
        "Get context from the document",
        `{}`,
        "RAGatouille",
        "RAG"
    )
];

export function get_commands(entityName){
    for (const item of commands)
    {
        item.entityName = entityName;
        item.app = "OnlyOffice Docx Editor (Word)"
    }

    return commands;
}
