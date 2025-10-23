import { CheckCircle, XCircle, GitBranch, FileCode } from 'lucide-react';

interface ApprovalDialogProps {
  approvalRequest: {
    id: string;
    title: string;
    description: string;
    template_data: any;
    expires_at: string;
  };
  workflow?: string;
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
  workflow: _workflow,  // Prefix with underscore to indicate intentionally unused
  intent,
  onApprove,
  onReject,
  isLoading = false,
}: ApprovalDialogProps) => {
  const { template_data } = approvalRequest;
  
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border-2 border-blue-300 p-4 shadow-md">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <GitBranch className="w-4 h-4 text-blue-600" />
            <h4 className="font-bold text-gray-900">{approvalRequest.title}</h4>
          </div>
          <p className="text-sm text-gray-600">{approvalRequest.description}</p>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={onReject}
            disabled={isLoading}
            className="px-3 py-1.5 bg-white border border-red-300 text-red-600 text-sm font-medium rounded hover:bg-red-50 transition-colors disabled:opacity-50 flex items-center gap-1.5"
          >
            <XCircle className="w-4 h-4" />
            Reject
          </button>
          <button
            onClick={onApprove}
            disabled={isLoading}
            className="px-4 py-1.5 bg-gradient-to-r from-green-500 to-green-600 text-white text-sm font-semibold rounded hover:from-green-600 hover:to-green-700 transition-colors disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
          >
            <CheckCircle className="w-4 h-4" />
            {isLoading ? 'Executing...' : 'Approve & Execute'}
          </button>
        </div>
      </div>

      <div className="bg-white rounded border border-blue-200 p-3 space-y-2">
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <span className="text-gray-500">Platform:</span>
            <span className="ml-1 font-medium text-blue-700">{intent.platform}</span>
          </div>
          <div>
            <span className="text-gray-500">Action:</span>
            <span className="ml-1 font-medium text-green-700">{intent.action}</span>
          </div>
          <div>
            <span className="text-gray-500">Confidence:</span>
            <span className="ml-1 font-medium text-purple-700">{(intent.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>

        {template_data && (
          <div className="border-t border-gray-200 pt-2">
            <div className="flex items-center gap-1.5 mb-1.5">
              <FileCode className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-xs font-semibold text-gray-700">Operation Details</span>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              {template_data.repository && (
                <div>
                  <span className="text-gray-500">Repository:</span>
                  <span className="ml-1 font-mono text-gray-900">{template_data.repository}</span>
                </div>
              )}
              {template_data.branch && (
                <div>
                  <span className="text-gray-500">Branch:</span>
                  <span className="ml-1 font-mono text-indigo-700">{template_data.branch}</span>
                </div>
              )}
              {template_data.commit_message && (
                <div className="col-span-2">
                  <span className="text-gray-500">Commit:</span>
                  <span className="ml-1 text-gray-900">{template_data.commit_message}</span>
                </div>
              )}
              {template_data.files && Object.keys(template_data.files).length > 0 && (
                <div className="col-span-2">
                  <span className="text-gray-500">Files:</span>
                  <span className="ml-1 text-gray-900">
                    {Object.keys(template_data.files).slice(0, 3).join(', ')}
                    {Object.keys(template_data.files).length > 3 && ` +${Object.keys(template_data.files).length - 3} more`}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
        ⏰ Expires: {new Date(approvalRequest.expires_at).toLocaleTimeString()}
      </div>
    </div>
  );
};

export default ApprovalDialog;
