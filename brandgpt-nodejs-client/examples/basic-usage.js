const { BrandGPTClient } = require('../dist/index');
const fs = require('fs');
const path = require('path');

async function main() {
  // Initialize client
  const client = new BrandGPTClient({
    baseUrl: 'https://brandgpt2.marcapo.com',
    apiKey: 'your-api-key-here' // Replace with actual API key
  });

  try {
    // Health check
    console.log('🔍 Checking API health...');
    const health = await client.health();
    console.log('✅ API is healthy:', health);

    // Get current user
    console.log('\n👤 Getting current user...');
    const user = await client.auth.getCurrentUser();
    console.log('✅ Current user:', user);

    // Create a session
    console.log('\n📝 Creating a new session...');
    const session = await client.sessions.create({
      name: 'Example Session'
    });
    console.log('✅ Session created:', session);

    // Example: Upload a text file (if available)
    const exampleFile = path.join(__dirname, 'example.txt');
    if (fs.existsSync(exampleFile)) {
      console.log('\n📄 Uploading document...');
      const fileBuffer = fs.readFileSync(exampleFile);
      const uploadResult = await client.ingestion.uploadFile(
        fileBuffer,
        'example.txt',
        session.id,
        { groupId: 'examples' }
      );
      console.log('✅ File uploaded:', uploadResult);

      // Wait a moment for processing
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Query the content
      console.log('\n🔍 Querying content...');
      const queryResult = await client.query.query({
        query: 'What is this document about?',
        sessionId: session.id
      });
      console.log('✅ Query result:', queryResult);
    }

    // Example: Ingest structured data
    console.log('\n📊 Ingesting structured data...');
    const structuredResult = await client.ingestion.ingestStructuredData({
      data: {
        product_name: 'Example Product',
        category: 'Technology',
        description: 'This is an example product for testing',
        features: ['Feature 1', 'Feature 2', 'Feature 3']
      },
      sessionId: session.id,
      groupId: 'products'
    });
    console.log('✅ Structured data ingested:', structuredResult);

    // List documents
    console.log('\n📋 Listing documents in session...');
    const documents = await client.documents.listBySession(session.id);
    console.log('✅ Documents:', documents);

    // List all sessions
    console.log('\n📋 Listing all sessions...');
    const sessions = await client.sessions.list();
    console.log('✅ Sessions:', sessions);

  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.statusCode) {
      console.error('Status Code:', error.statusCode);
    }
    if (error.details) {
      console.error('Details:', error.details);
    }
  }
}

// Create example text file if it doesn't exist
const exampleFile = path.join(__dirname, 'example.txt');
if (!fs.existsSync(exampleFile)) {
  fs.writeFileSync(exampleFile, `
This is an example text document for testing the BrandGPT API.

It contains some sample content that can be ingested and queried.

Key topics:
- API testing
- Document ingestion
- Content querying
- RAG (Retrieval Augmented Generation)

This document demonstrates how to use the BrandGPT Node.js client library.
`.trim());
  console.log('📝 Created example.txt for testing');
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { main };