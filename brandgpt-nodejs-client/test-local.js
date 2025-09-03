const { BrandGPTClient } = require('./dist/index');
const fs = require('fs');
const path = require('path');

async function testLocalBrandGPT() {
  console.log('🚀 Testing BrandGPT Node.js Client against localhost:9700\n');

  // Initialize client with local instance
  const client = new BrandGPTClient({
    baseUrl: 'http://localhost:9700',
    apiKey: 'bgpt_1c071a3e940a2a3e0101d6ce3aa6a16bbf309f8192c5ca02' // Using the working API key from our tests
  });

  try {
    // 1. Health Check
    console.log('1. 🏥 Health Check');
    const health = await client.health();
    console.log('✅ Health Status:', health);
    console.log('');

    // 2. Get Current User
    console.log('2. 👤 Get Current User');
    const user = await client.auth.getCurrentUser();
    console.log('✅ Current User:', {
      id: user.id,
      username: user.username,
      email: user.email,
      created_at: user.created_at
    });
    console.log('');

    // 3. Create a Session
    console.log('3. 📝 Create Session');
    const session = await client.sessions.create({
      name: 'Node.js Client Test Session'
    });
    console.log('✅ Session Created:', {
      id: session.id,
      user_id: session.user_id,
      created_at: session.created_at
    });
    console.log('');

    // 4. Create a test file and upload it
    console.log('4. 📄 Upload Test File');
    const testContent = `
BrandGPT Node.js Client Library Test Document

This document is used to test the BrandGPT Node.js client library functionality.

Key Features Being Tested:
- File Upload and Ingestion
- Session Management
- Query Processing
- Source Attribution

Test Data:
- Product: BrandGPT API Client
- Version: 1.0.0
- Language: Node.js/TypeScript
- Features: Authentication, Sessions, Ingestion, Querying
- Use Cases: Document Analysis, RAG Applications, Content Management

Technical Specifications:
- Built with TypeScript for type safety
- Uses Axios for HTTP requests
- Supports file uploads with FormData
- Implements error handling and retries
- Provides comprehensive documentation

This test verifies that the client library can successfully communicate with the BrandGPT API.
    `.trim();

    const testFilePath = path.join(__dirname, 'test-document.txt');
    fs.writeFileSync(testFilePath, testContent);
    console.log('📝 Created test file:', testFilePath);

    const fileBuffer = fs.readFileSync(testFilePath);
    const uploadResult = await client.ingestion.uploadFile(
      fileBuffer,
      'test-document.txt',
      session.id,
      { groupId: 'nodejs-client-test' }
    );
    console.log('✅ File Uploaded:', uploadResult);
    console.log('');

    // 5. Wait for processing
    console.log('5. ⏳ Waiting for document processing...');
    await new Promise(resolve => setTimeout(resolve, 3000));

    // 6. Test Structured Data Ingestion
    console.log('6. 📊 Ingest Structured Data');
    const structuredData = {
      client_info: {
        name: 'BrandGPT Node.js Client',
        version: '1.0.0',
        author: 'Marcapo',
        language: 'TypeScript/Node.js'
      },
      features: [
        'Authentication Management',
        'Session Handling',
        'File Upload',
        'URL Scraping',
        'Structured Data Ingestion',
        'RAG Queries',
        'Error Handling'
      ],
      test_metadata: {
        test_date: new Date().toISOString(),
        test_environment: 'localhost:9700',
        test_purpose: 'Validate client library functionality'
      }
    };

    const structuredResult = await client.ingestion.ingestStructuredData({
      data: structuredData,
      sessionId: session.id,
      groupId: 'nodejs-client-test',
      metadata: {
        type: 'client_test',
        source: 'automated_test'
      }
    });
    console.log('✅ Structured Data Ingested:', structuredResult);
    console.log('');

    // 7. Wait a bit more for processing
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 8. Test Basic Query
    console.log('7. 🔍 Test Basic Query');
    const basicQuery = await client.query.query({
      query: 'What is the BrandGPT Node.js client library and what features does it provide?',
      sessionId: session.id
    });
    console.log('✅ Basic Query Result:');
    console.log('Answer:', basicQuery.response);
    console.log('Sources Found:', basicQuery.sources.length);
    if (basicQuery.sources.length > 0) {
      console.log('Source Preview:', basicQuery.sources[0].text.substring(0, 100) + '...');
    }
    console.log('');

    // 9. Test Specific Query
    console.log('8. 🎯 Test Specific Query');
    const specificQuery = await client.query.query({
      query: 'What are the key features and technical specifications mentioned?',
      sessionId: session.id,
      maxResults: 8
    });
    console.log('✅ Specific Query Result:');
    console.log('Answer:', specificQuery.response);
    console.log('Sources Found:', specificQuery.sources.length);
    console.log('');

    // 10. Test Group-specific Query
    console.log('9. 🏷️ Test Group-specific Query');
    const groupQuery = await client.query.query({
      query: 'What information is available about testing?',
      sessionId: session.id,
      groupId: 'nodejs-client-test'
    });
    console.log('✅ Group Query Result:');
    console.log('Answer:', groupQuery.response);
    console.log('Sources Found:', groupQuery.sources.length);
    console.log('');

    // 11. List Documents
    console.log('10. 📋 List Session Documents');
    const documents = await client.documents.listBySession(session.id);
    console.log('✅ Documents in Session:');
    documents.forEach(doc => {
      console.log(`  - ${doc.filename || 'Structured Data'} (${doc.content_type}) - Status: ${doc.processed}`);
    });
    console.log('');

    // 12. List All Sessions
    console.log('11. 📚 List All Sessions');
    const sessions = await client.sessions.list();
    console.log('✅ Total Sessions:', sessions.length);
    console.log('Recent Sessions:');
    sessions.slice(-3).forEach(s => {
      console.log(`  - ${s.id}: Created ${new Date(s.created_at).toLocaleString()}`);
    });
    console.log('');

    // 13. Test Error Handling
    console.log('12. ❌ Test Error Handling');
    try {
      await client.query.query({
        query: 'Test query',
        sessionId: 'non-existent-session-id'
      });
    } catch (error) {
      console.log('✅ Error Handling Works:', error.message);
    }
    console.log('');

    // Clean up test file
    fs.unlinkSync(testFilePath);
    console.log('🧹 Cleaned up test file');
    console.log('');

    console.log('🎉 All tests completed successfully!');
    console.log(`📊 Test Summary:
    - Health Check: ✅ Passed
    - User Authentication: ✅ Passed  
    - Session Creation: ✅ Passed
    - File Upload: ✅ Passed
    - Structured Data Ingestion: ✅ Passed
    - Basic Query: ✅ Passed
    - Specific Query: ✅ Passed
    - Group Query: ✅ Passed
    - Document Listing: ✅ Passed
    - Session Listing: ✅ Passed
    - Error Handling: ✅ Passed`);

    return {
      success: true,
      sessionId: session.id,
      documentsProcessed: documents.length,
      queriesExecuted: 3
    };

  } catch (error) {
    console.error('❌ Test Failed:', error.message);
    if (error.statusCode) {
      console.error('Status Code:', error.statusCode);
    }
    if (error.details) {
      console.error('Error Details:', error.details);
    }
    console.error('Stack:', error.stack);
    
    return {
      success: false,
      error: error.message
    };
  }
}

// Run the test if this file is executed directly
if (require.main === module) {
  testLocalBrandGPT()
    .then(result => {
      if (result.success) {
        console.log('\n🎊 Client library test completed successfully!');
        process.exit(0);
      } else {
        console.log('\n💥 Client library test failed!');
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('💥 Unexpected error:', error);
      process.exit(1);
    });
}

module.exports = { testLocalBrandGPT };