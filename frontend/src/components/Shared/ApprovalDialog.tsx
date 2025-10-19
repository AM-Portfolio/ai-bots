import { CheckCircle, XCircle, FileText, AlertCircle } from 'lucide-react';

interface ApprovalDialogProps {
  approvalRequest: {
    id: string;
    title: string;
    description: string;
    template_data: any;
    expires_at: string;
  };
  workflow: string;
  intent: {
    platform: string;
    action: string;
    confidence: number;
  };
  onApprove: () => void;
  onReject: () => void;
  isLoading?: boolean;
}

const ApprovalDialog = ({
  approvalRequest,
  workflow,
  intent,
  onApprove,
  onReject,
  isLoading = false,
}: ApprovalDialogProps) => {
  return (
    <div className="bg-white rounded-xl shadow-lg border-2 border-blue-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-6 py-4">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-6 h-6" />
          <div>
            <h3 className="text-lg font-bold">Approval Required</h3>
            <p className="text-sm text-blue-100">{approvalRequest.title}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-4">
        {/* Description */}
        <div>
          <label className="text-sm font-semibold text-gray-700 block mb-1">Description</label>
          <p className="text-gray-600">{approvalRequest.description}</p>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-semibold text-gray-700 block mb-1">Platform</label>
            <span className="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium">
              {intent.platform}
            </span>
          </div>
          <div>
            <label className="text-sm font-semibold text-gray-700 block mb-1">Action</label>
            <span className="inline-flex items-center px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm font-medium">
              {intent.action}
            </span>
          </div>
          <div>
            <label className="text-sm font-semibold text-gray-700 block mb-1">Workflow</label>
            <span className="inline-flex items-center px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm font-medium">
              {workflow}
            </span>
          </div>
          <div>
            <label className="text-sm font-semibold text-gray-700 block mb-1">Confidence</label>
            <span className="inline-flex items-center px-3 py-1 bg-yellow-50 text-yellow-700 rounded-full text-sm font-medium">
              {(intent.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Template Data */}
        <div>
          <label className="text-sm font-semibold text-gray-700 block mb-2 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Template Details
          </label>
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <pre className="text-xs text-gray-700 overflow-x-auto">
              {JSON.stringify(approvalRequest.template_data, null, 2)}
            </pre>
          </div>
        </div>

        {/* Expiration Notice */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <p className="text-sm text-amber-800">
            ⏰ <strong>Expires:</strong> {new Date(approvalRequest.expires_at).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bg-gray-50 px-6 py-4 flex gap-3 justify-end border-t border-gray-200">
        <button
          onClick={onReject}
          disabled={isLoading}
          className="px-6 py-2.5 bg-white border-2 border-red-300 text-red-700 font-semibold rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <XCircle className="w-5 h-5" />
          Reject
        </button>
        <button
          onClick={onApprove}
          disabled={isLoading}
          className="px-6 py-2.5 bg-gradient-to-r from-green-500 to-green-600 text-white font-semibold rounded-lg hover:from-green-600 hover:to-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm"
        >
          <CheckCircle className="w-5 h-5" />
          {isLoading ? 'Processing...' : 'Approve & Execute'}
        </button>
      </div>
    </div>
  );
};

export default ApprovalDialog;
