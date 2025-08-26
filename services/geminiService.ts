
import { GoogleGenAI, Type } from "@google/genai";
import type { InvestigationData, Entity } from '../types';
import { EntityType } from '../types';

if (!process.env.API_KEY) {
    throw new Error("API_KEY environment variable not set");
}

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const entityTypes = Object.values(EntityType);

const responseSchema = {
    type: Type.OBJECT,
    properties: {
        entities: {
            type: Type.ARRAY,
            description: "A list of all discovered entities.",
            items: {
                type: Type.OBJECT,
                properties: {
                    id: { type: Type.INTEGER, description: "A unique integer ID for the entity." },
                    type: { type: Type.STRING, enum: entityTypes, description: "The category of the entity." },
                    label: { type: Type.STRING, description: "The value or name of the entity (e.g., 'example.com', 'user@example.com')." }
                },
                required: ["id", "type", "label"]
            }
        },
        relations: {
            type: Type.ARRAY,
            description: "A list of relationships connecting the entities.",
            items: {
                type: Type.OBJECT,
                properties: {
                    from: { type: Type.INTEGER, description: "The ID of the source entity." },
                    to: { type: Type.INTEGER, description: "The ID of the target entity." },
                    label: { type: Type.STRING, description: "A brief description of the relationship (e.g., 'A Record', 'Leaked In', 'Owner Of')." }
                },
                required: ["from", "to", "label"]
            }
        }
    },
    required: ["entities", "relations"]
};

const callGeminiWithRetry = async (prompt: string, schema?: typeof responseSchema) => {
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: prompt,
            config: {
                responseMimeType: schema ? "application/json" : "text/plain",
                responseSchema: schema,
            },
        });
        
        const text = response.text.trim();
        if (!text) {
             throw new Error("Received empty response from AI.");
        }
        return text;

    } catch (error) {
        console.error("Error communicating with Gemini API:", error);
        throw new Error("Failed to get a valid response from the AI model.");
    }
}


/**
 * Simulates an OSINT investigation by generating mock data using Gemini.
 */
export const runInvestigation = async (searchTerm: string): Promise<InvestigationData> => {
    const prompt = `
        You are an OSINT data simulator for a cybersecurity analysis tool. For the target "${searchTerm}", generate a plausible but fictional set of related entities and the relationships between them.
        The result must be a graph of interconnected data points. Create at least 8-15 entities and a similar number of relations to build a rich graph.
        Ensure the entity IDs are unique integers starting from 1.
        Output ONLY a valid JSON object that strictly adheres to the provided schema. Do not include any explanatory text or markdown formatting.
    `;

    const jsonText = await callGeminiWithRetry(prompt, responseSchema);
    const data = JSON.parse(jsonText);

    if (!data.entities || !data.relations) {
        throw new Error("Invalid data structure received from AI.");
    }

    return data as InvestigationData;
};

/**
 * Generates a detailed analytical report from the investigation data using Gemini.
 */
export const generateReport = async (data: InvestigationData): Promise<string> => {
    const dataString = JSON.stringify(data, null, 2);

    const prompt = `
        You are a senior cybersecurity analyst and OSINT specialist. Your task is to write a comprehensive, insightful, and actionable intelligence report based on the following structured data.

        **Data:**
        \`\`\`json
        ${dataString}
        \`\`\`

        **Report Requirements (Follow this structure precisely):**
        
        # OSINT Analysis Report

        ## 1. Executive Summary
        Start with a concise, high-level overview of the most critical findings and potential risks associated with the target. Answer the "so what?" question immediately.

        ## 2. Key Findings
        Use a bulleted list to highlight the most significant pieces of intelligence discovered. Each point should be a clear, verifiable fact from the data.
        * Example: The IP address 192.0.2.1 is linked to both 'example.com' and a known data breach.

        ## 3. Entity Relationship Analysis
        Detail the connections between the discovered entities. Explain what the relationships (e.g., 'Resolves To', 'Leaked In', 'Member Of') imply in this context. Go beyond just listing connections; interpret their significance.

        ## 4. Threat Assessment & Hypotheses
        - **Identify Potential Threats:** Based on the connections, identify potential threats, attack vectors, or vulnerabilities (e.g., exposed infrastructure, potential for spear-phishing, credential stuffing risk).
        - **Formulate Hypotheses:** Propose clear, testable hypotheses based on the data. These should be educated guesses about potential activities or risks. (e.g., "Hypothesis: The username '...' found in the '...' breach is likely used across multiple platforms, making those accounts vulnerable if password reuse is occurring.").

        ## 5. Hidden Pattern & Anomaly Detection
        Analyze the complete dataset to identify any subtle patterns, unusual connections, or data points that seem out of place. Is there an entity that links two otherwise disconnected clusters? Is there a suspicious concentration of certain entity types?
        
        ## 6. Recommendations & Next Steps
        Provide a bulleted list of actionable recommendations for the next phase of the investigation or for mitigating identified risks.
        * Example: Conduct a vulnerability scan on IP address 1.2.3.4.
        * Example: Monitor paste sites for activity related to the email address '...'.

        **Formatting:**
        Use professional, clear language. Use Markdown headings, **bold text** for emphasis, and lists to ensure the report is scannable and easy to comprehend. Do not add any preamble or conversational text. Begin directly with the H1 title.
    `;

    return callGeminiWithRetry(prompt);
};


/**
 * Expands the analysis for a specific entity with standard OSINT investigation.
 */
export const expandEntityAnalysis = async (entity: Entity, context: InvestigationData): Promise<InvestigationData> => {
    const contextString = JSON.stringify(context, null, 2);
    const maxId = Math.max(0, ...context.entities.map(e => e.id));

    const prompt = `
      You are an OSINT data simulator expanding an existing investigation. The user has clicked on a specific entity and wants more details.
      
      **Existing Investigation Data:**
      \`\`\`json
      ${contextString}
      \`\`\`
      
      **Target Entity for Expansion:**
      - ID: ${entity.id}
      - Type: ${entity.type}
      - Label: "${entity.label}"

      **Your Task:**
      1.  Generate 2-4 **new** plausible but fictional entities that are directly or indirectly related to the **Target Entity**.
      2.  Generate the relationships connecting these new entities to the Target Entity or to each other.
      3.  **Crucially, assign new, unique integer IDs to your new entities, starting from ${maxId + 1}.** Do not reuse any existing IDs from the context.
      4.  The output must contain ONLY the new entities and new relations. Do not repeat any data from the existing investigation.
      5.  Output ONLY a valid JSON object that strictly adheres to the provided schema. Do not include any explanatory text or markdown formatting.
    `;
    
    const jsonText = await callGeminiWithRetry(prompt, responseSchema);
    const data = JSON.parse(jsonText);

    if (!data.entities || !data.relations) {
        throw new Error("Invalid data structure received from AI for expansion.");
    }

    return data as InvestigationData;
}

/**
 * Performs a deep, simulated forensic analysis on a file-like entity.
 */
export const performDeepAnalysisOnEntity = async (entity: Entity, context: InvestigationData): Promise<InvestigationData> => {
    const contextString = JSON.stringify(context, null, 2);
    const maxId = Math.max(0, ...context.entities.map(e => e.id));

    const prompt = `
        You are a world-class digital forensics and database recovery expert. The user is performing a deep-dive forensic analysis on an entity representing a data file or breach.
        Your mission is to **deconstruct and decrypt** the contents of this entity, extracting every possible artifact.

        **Existing Investigation Context:**
        \`\`\`json
        ${contextString}
        \`\`\`

        **Target Entity for Deep Forensic Analysis:**
        - ID: ${entity.id}
        - Type: ${entity.type}
        - Label: "${entity.label}"

        **Your Mission (MANDATORY):**
        1.  **Simulate and Deconstruct Contents:** Based on the entity's label (e.g., "UserDB_dump_2022.sql", "Corporate_Credentials.zip"), you must simulate the raw data inside. For an SQL dump, this means you MUST simulate and then deconstruct the \`INSERT INTO users (username, email, password_hash) VALUES (...)\` statements. For a general breach, simulate a raw text file of \`email:password\` pairs.
        2.  **Exhaustive Extraction (Leave No Stone Unturned):** From your simulated contents, generate a comprehensive list of 8-15 **new** fictional entities. You MUST include a rich variety of types: **Email, Username, Password, PasswordHash (bcrypt format), IP, SessionInfo, APIKey, and Cookie.**
        3.  **Establish Forensic Links:** For EVERY new entity you create, you MUST create a relation linking it back to the original Target Entity (ID: ${entity.id}). The relationship label MUST be forensically specific, such as "Contains Credential", "Leaked Hash", "Source IP", or "Found In Dump".
        4.  **Assign Unique IDs:** Assign new, unique integer IDs to all your new entities, starting from ${maxId + 1}. Do NOT reuse any IDs from the existing context.
        5.  **Output Format:** The output must contain ONLY the new entities and new relations. Do not repeat any data from the existing investigation. Output ONLY a valid JSON object that strictly adheres to the provided schema. No markdown or explanations.
    `;

    const jsonText = await callGeminiWithRetry(prompt, responseSchema);
    const data = JSON.parse(jsonText);

    if (!data.entities || !data.relations) {
        throw new Error("Invalid data structure received from AI for deep analysis.");
    }

    return data as InvestigationData;
}