### LLManuals - Technical Document

---

#### **1. Overview**

This document outlines the architecture and functionality of a serverless customer support tool designed to help businesses manage and provide automated support through a knowledge-based system. Leveraging AWS's robust cloud infrastructure, this application enables businesses to offer a question-answering service that integrates seamlessly with their websites or other platforms. The application uses Amazon Bedrock for Retrieval-Augmented Generation (RAG), allowing it to respond to customer queries based on the business's provided knowledge.

---

#### **2. Architecture**

The application's architecture is built on AWS's serverless technologies, ensuring scalability, reliability, and cost-effectiveness. Key components include:

- **AWS Lambda**: Each function encapsulates specific business logic, such as managing knowledge bases, handling customer queries, and interfacing with Amazon Bedrock. Functions are triggered by API Gateway, providing RESTful endpoints for external integrations.

- **Amazon API Gateway**: This acts as the frontend for all API requests, routing them securely to the appropriate Lambda functions. It is secured with Cognito-based authorization to ensure only authenticated requests are processed.

- **Amazon Cognito**: Provides user authentication and authorization, securing the admin panel and API endpoints. Businesses can manage their user accounts and control access to different parts of the application.

- **Amazon S3**: Stores static files (e.g., documents, PDFs) and web-based knowledge resources uploaded by businesses. The application uses these resources to build the knowledge base for answering customer queries.

- **Amazon DynamoDB**: A managed NoSQL database that stores metadata, user profiles, and other application data. It supports fast, flexible data access patterns, essential for real-time customer interactions.

- **AWS Step Functions**: Orchestrates complex workflows such as web scraping tasks and data synchronization, ensuring the smooth ingestion of knowledge into the system.

- **Amazon Bedrock**: Central to the RAG process, Bedrock performs the Retrieval-Augmented Generation tasks, using the knowledge provided by businesses to generate accurate responses to customer queries.

---

#### **3. Key Features**

1. **Knowledge Management**:
   - **Static Files and URLs**: Businesses can upload documents or provide URLs as knowledge sources. These resources are ingested into the system and used by Bedrock to generate responses.
   - **Admin Panel**: An easy-to-use interface allows businesses to manage their knowledge base, monitor usage, and configure their API integrations.

2. **Automated Customer Support**:
   - **Real-Time Question Answering**: Customers can ask questions via the integrated API, and the system responds based on the ingested knowledge.
   - **Public Data Compliance**: The system strictly works with publicly available data, ensuring compliance with legal requirements.

3. **Security and Access Control**:
   - **Cognito-Backed Authorization**: Ensures that only authenticated users can access the admin panel and API endpoints.
   - **Encrypted Data Storage**: Sensitive data is stored securely in DynamoDB and S3.

4. **Scalability and Cost-Efficiency**:
   - **Serverless Infrastructure**: Automatically scales with demand, ensuring performance during peak usage without the need for manual scaling.
   - **Pay-As-You-Go**: Costs are minimized as you only pay for the compute time and storage you actually use.

5. **Integration Flexibility**:
   - **API Integration**: Businesses can integrate the support tool with their website or application using the provided API, enabling seamless customer interaction.

---

#### **5. Use Cases**

###### **1. User Registration and Authentication**

**Actors**: Business Users (Admin), Cognito

**Description**: The registration and authentication process is seamlessly managed by Amazon Cognito, ensuring a secure and reliable user experience. Business users interact directly with the Cognito API to sign up, verify their accounts, and obtain authentication tokens necessary for accessing the admin panel and API.

**Steps**:
1. **Sign Up**: The business user accesses a sign-up form on the application’s website. They enter required details such as email, password, and preferred username.
2. **Account Verification**: Cognito sends a verification email to the user. The user verifies their account by clicking on the link provided.
3. **Token Retrieval**: Upon successful login, Cognito issues tokens (ID, access, and refresh tokens) which the user stores for subsequent authenticated requests to the application’s API.

**Outcome**: The business user is successfully registered and authenticated, gaining access to the admin panel and other application features.

---

###### **2. Subscription and Environment Creation**

**Actors**: Business Users (Admin), AWS Lambda, Amazon Bedrock, DynamoDB, S3

**Description**: Upon subscribing, a personalized environment is created for the business. This environment includes the creation of a Bedrock agent tailored to the business's needs, along with a connected knowledge base composed of two data sources: one for static files and another for web-scraped data.

**Steps**:
1. **Subscription**: The business user subscribes to the service, initiating the environment creation process.
2. **Environment Setup**:
   - **Bedrock Agent Creation**: A new Bedrock agent is created, initialized with the business’s name and description as instructions.
   - **Knowledge Base Setup**: Two data sources are created:
     - **Static Files Source**: For documents and files uploaded by the business.
     - **Scraped Data Source**: For data gathered via web scraping, relevant to the business’s operations.
   - **Database and Storage Configuration**: DynamoDB tables are set up to store metadata, and S3 buckets are provisioned for file storage.
3. **Environment Initialization**: The agent, knowledge base, and data sources are linked and prepared to ingest and process information.

**Outcome**: The business now has a dedicated environment within the application, ready for managing and processing knowledge relevant to its operations.

---

###### **3. Knowledge Management**

**Actors**: Business Users (Admin), AWS Lambda, S3, DynamoDB, Amazon Bedrock

**Description**: The business can manage its knowledge resources through an intuitive admin panel. This includes listing existing knowledge, adding new knowledge (via file uploads or URLs), deleting outdated or irrelevant information, and synchronizing the knowledge base with the Bedrock agent.

**Steps**:
1. **Listing Knowledge**:
   - The admin panel displays a list of current knowledge items from both static files and web sources.
2. **Adding Knowledge**:
   - **Static Files**: The user uploads documents or files to the S3 bucket via the admin panel.
   - **Web Sources**: The user provides URLs to be scraped and processed.
   - Metadata for these sources is stored in DynamoDB.
3. **Deleting Knowledge**:
   - The user selects items to delete, triggering Lambda functions that remove the data from S3 and update DynamoDB records.
4. **Synchronizing Knowledge**:
   - The user initiates a synchronization process that triggers workflows in AWS Step Functions to ingest and process new knowledge into the Bedrock agent.
   - This ensures that the Bedrock agent is up-to-date with the latest information provided by the business.

**Outcome**: The business has complete control over its knowledge base, ensuring that the Bedrock agent always reflects the most current and relevant information for answering customer queries.

---

###### **4. Monitoring Agent and Task Statuses**

**Actors**: Business Users (Admin), AWS Lambda, Amazon Bedrock, DynamoDB, CloudWatch

**Description**: The admin panel provides real-time status updates for the Bedrock agent and knowledge tasks. This allows the business to monitor the health and effectiveness of the support tool.

**Steps**:
1. **Agent Status Monitoring**:
   - The admin panel displays the current status of the Bedrock agent, including its readiness to process queries and any ongoing updates.
2. **Knowledge Task Statuses**:
   - The statuses of ongoing or completed knowledge synchronization tasks are shown, providing insight into data ingestion and processing activities, as well as their results.

**Outcome**: The business has visibility into the operational status of its customer support environment, allowing for proactive management and quick resolution of any issues.

---

###### **5. Account Deletion and Data Cleanup**

**Actors**: Business Users (Admin), AWS Lambda, S3, DynamoDB, Amazon Bedrock

**Description**: If the business decides to terminate its subscription, the application provides a process for securely deleting all associated data, ensuring compliance with data privacy regulations.

**Steps**:
1. **Account Deletion Request**:
   - The business initiates an account deletion request via the admin panel.
2. **Data Cleanup**:
   - **Knowledge Base**: All knowledge data (static files, web sources) is deleted from S3 and DynamoDB.
   - **Bedrock Agent**: The Bedrock agent and its associated knowledge base are terminated.
   - **User Data**: All user-related data is removed from Cognito and DynamoDB.

**Outcome**: The business’s environment, including all knowledge and user data, is completely and securely removed from the system, ensuring no residual data remains.

---

###### **6. Querying Bedrock via API Integration**

**Actors**: End Users, Business Servers, AWS API Gateway, AWS Lambda, Amazon Bedrock

**Description**: This use case involves the business integrating the customer support tool's API into their own web service, such as a website or mobile app. The end users interact with this service by sending prompts (questions or queries). The business's server forwards these requests to the application’s API, authenticates using their token, and then returns the response generated by the Bedrock agent back to the end user.

**Steps**:

1. **API Integration**:
   - The business integrates the API into their web service by setting up an endpoint on their server that acts as a tunnel for user queries.
   - This endpoint is configured to forward requests to the application’s API hosted on AWS.

2. **End User Interaction**:
   - End users interact with the business's web service by submitting prompts (e.g., typing a question into a chatbox on the website).
   - The prompt is sent to the business’s server, where it is processed and prepared for forwarding.

3. **Request Forwarding**:
   - The business’s server receives the prompt and forwards it to the application’s API Gateway.
   - The server includes the necessary authentication token (obtained during the initial setup) in the request headers to authenticate the request.

4. **Processing by Bedrock**:
   - The API Gateway routes the request to the appropriate AWS Lambda function.
   - The Lambda function forwards the prompt to the Bedrock agent, which uses the business’s knowledge base to generate a response.
   - Bedrock processes the prompt, leveraging the Retrieval-Augmented Generation (RAG) model, and returns a generated answer based on the ingested knowledge, quoting text and citing sources.

5. **Response Handling**:
   - The Lambda function receives the response from Bedrock and sends it back through the API Gateway to the business’s server.
   - The business’s server receives the response and forwards it to the end user’s interface (e.g., displays the answer in the chatbox).

6. **End User Receives Response**:
   - The end user sees the response generated by Bedrock as if it were coming directly from the business’s own service.
   - This creates a seamless user experience where the end user interacts directly with the business’s platform while benefiting from the advanced question-answering capabilities provided by the Bedrock agent.

**Outcome**: The business successfully integrates the customer support tool into their service, enabling end users to receive real-time, accurate responses to their queries based on the business’s knowledge. This enhances the end user experience while maintaining the business’s brand and control over the interaction.

---

#### **6. Conclusion**

This serverless customer support tool on AWS offers businesses a powerful, scalable, and secure solution for providing automated customer support. By leveraging AWS services such as Lambda, API Gateway, Cognito, S3, DynamoDB, and Bedrock, the application ensures that businesses can efficiently manage their knowledge base and provide real-time support to their customers. The serverless architecture minimizes costs and maintenance overhead, making it an ideal choice for businesses of all sizes.

This document provides a comprehensive overview of the application’s architecture, features, and benefits, making it clear why this solution is a compelling choice for any business looking to enhance their customer support capabilities.
