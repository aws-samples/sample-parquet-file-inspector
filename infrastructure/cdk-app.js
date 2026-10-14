/**
 * Parquet File Inspector - AWS CDK Infrastructure
 *
 * Deploys a static website (S3 + CloudFront) for the Parquet File Inspector.
 * The application is entirely client-side - no Lambda, no API Gateway.
 *
 * Resources created:
 *   - S3 Bucket (private, BlockPublicAccess.BLOCK_ALL)
 *   - CloudFront Distribution with Origin Access Control (OAC)
 *   - CloudFront Function for SPA path rewriting
 *   - BucketDeployment (uploads frontend + demo Parquet file)
 *
 * Usage:
 *   cd infrastructure
 *   npm install
 *   cdk deploy
 */

const cdk = require('aws-cdk-lib');
const s3 = require('aws-cdk-lib/aws-s3');
const s3deploy = require('aws-cdk-lib/aws-s3-deployment');
const cloudfront = require('aws-cdk-lib/aws-cloudfront');
const origins = require('aws-cdk-lib/aws-cloudfront-origins');
const path = require('path');

class ParquetInspectorStack extends cdk.Stack {
  constructor(scope, id, props) {
    super(scope, id, props);

    // --- S3 Bucket ---
    // Private bucket - only accessible via CloudFront OAC.
    // autoDeleteObjects + DESTROY policy for easy teardown (this is a demo tool,
    // not a production data store).
    const bucket = new s3.Bucket(this, 'WebsiteBucket', {
      bucketName: `parquet-inspector-${this.account}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      // Deny any request not using TLS (adds an aws:SecureTransport=false Deny
      // to the bucket policy). Required by Baseline Security Control 17.
      enforceSSL: true,
      minimumTLSVersion: 1.2,
    });

    // --- CloudFront Origin Access Control ---
    // Allows CloudFront to read from the private S3 bucket without making it public.
    const oac = new cloudfront.S3OriginAccessControl(this, 'OAC', {
      signing: cloudfront.Signing.SIGV4_NO_OVERRIDE,
    });

    // --- CloudFront Function (viewer-request) ---
    // Rewrites non-file paths to /index.html for SPA-style routing.
    // Without this, paths like /structure would return S3 403 (no such key).
    const rewriteFunction = new cloudfront.Function(this, 'SpaRewriteFunction', {
      code: cloudfront.FunctionCode.fromInline(`
        function handler(event) {
          var request = event.request;
          var uri = request.uri;
          // Only rewrite paths that don't contain a file extension
          // (preserves .parquet, .wasm, .js, .mjs, .html requests)
          if (uri !== '/' && !uri.includes('.')) {
            request.uri = '/index.html';
          }
          return request;
        }
      `),
      comment: 'Rewrites non-file paths to index.html for SPA routing',
    });

    // --- CloudFront Distribution ---
    const distribution = new cloudfront.Distribution(this, 'Distribution', {
      comment: 'Parquet File Inspector',
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(bucket, {
          originAccessControl: oac,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        functionAssociations: [{
          function: rewriteFunction,
          eventType: cloudfront.FunctionEventType.VIEWER_REQUEST,
        }],
      },
      defaultRootObject: 'index.html',
      // Return index.html for 403 errors (S3 returns 403 for missing keys with OAC)
      errorResponses: [{
        httpStatus: 403,
        responseHttpStatus: 200,
        responsePagePath: '/index.html',
      }],
    });

    // --- Content Deployment ---
    // Uploads the frontend app and any demo Parquet files to S3.
    // Automatically invalidates the CloudFront cache on deploy.
    new s3deploy.BucketDeployment(this, 'DeploySite', {
      sources: [
        s3deploy.Source.asset(path.join(__dirname, '..', 'src', 'frontend')),
        s3deploy.Source.asset(path.join(__dirname, '..', 'sample-data')),
      ],
      destinationBucket: bucket,
      distribution,
      distributionPaths: ['/*'],
      // Set correct MIME type for .wasm files (critical for WebAssembly.compile)
      contentType: undefined, // Let S3 auto-detect; we handle .wasm via deploy script
    });

    // --- Stack Outputs ---
    new cdk.CfnOutput(this, 'WebsiteURL', {
      value: `https://${distribution.distributionDomainName}`,
      description: 'Parquet File Inspector URL',
    });
    new cdk.CfnOutput(this, 'BucketName', {
      value: bucket.bucketName,
      description: 'S3 bucket name (for manual uploads)',
    });
    new cdk.CfnOutput(this, 'DistributionId', {
      value: distribution.distributionId,
      description: 'CloudFront distribution ID (for cache invalidation)',
    });
  }
}

// --- App Entry Point ---
const app = new cdk.App();
new ParquetInspectorStack(app, 'ParquetInspectorStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  description: 'Parquet File Inspector - browser-based Parquet structure viewer',
});
