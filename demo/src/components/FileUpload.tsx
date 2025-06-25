import React, { useState } from 'react';
import { UploadIcon, FileIcon, XIcon, CheckIcon } from 'lucide-react';
interface FileUploadProps {
  language: string;
  onFileUpload: (files: File[]) => void;
}
export const FileUpload: React.FC<FileUploadProps> = ({
  language,
  onFileUpload
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const translations = {
    title: {
      en: 'Upload Your Tax Documents',
      es: 'Suba Sus Documentos Fiscales'
    },
    subtitle: {
      en: 'Drag and drop your files here or click to browse',
      es: 'Arrastre y suelte sus archivos aquí o haga clic para buscar'
    },
    accepted: {
      en: 'Accepted file types: PDF, JPG, PNG',
      es: 'Tipos de archivos aceptados: PDF, JPG, PNG'
    },
    uploadButton: {
      en: 'Browse Files',
      es: 'Buscar Archivos'
    },
    uploadedFiles: {
      en: 'Uploaded Files',
      es: 'Archivos Subidos'
    },
    success: {
      en: 'Successfully uploaded',
      es: 'Subido con éxito'
    }
  };
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      setFiles(prevFiles => [...prevFiles, ...newFiles]);
      onFileUpload(newFiles);
    }
  };
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setFiles(prevFiles => [...prevFiles, ...newFiles]);
      onFileUpload(newFiles);
    }
  };
  const removeFile = (index: number) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };
  return <div className="bg-white rounded-lg shadow p-6 mb-8">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">
        {translations.title[language as keyof typeof translations.title]}
      </h2>
      <div className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center text-center
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`} onDragEnter={handleDragEnter} onDragLeave={handleDragLeave} onDragOver={handleDragOver} onDrop={handleDrop}>
        <UploadIcon className="w-12 h-12 text-blue-500 mb-4" />
        <p className="text-gray-700 mb-2">
          {translations.subtitle[language as keyof typeof translations.subtitle]}
        </p>
        <p className="text-sm text-gray-500 mb-4">
          {translations.accepted[language as keyof typeof translations.accepted]}
        </p>
        <label className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg cursor-pointer transition-colors">
          {translations.uploadButton[language as keyof typeof translations.uploadButton]}
          <input type="file" className="hidden" multiple onChange={handleFileChange} accept=".pdf,.jpg,.jpeg,.png" />
        </label>
      </div>
      {files.length > 0 && <div className="mt-6">
          <h3 className="font-medium text-gray-700 mb-3">
            {translations.uploadedFiles[language as keyof typeof translations.uploadedFiles]}{' '}
            ({files.length})
          </h3>
          <ul className="space-y-2">
            {files.map((file, index) => <li key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                <div className="flex items-center">
                  <FileIcon className="w-5 h-5 text-blue-500 mr-3" />
                  <span className="text-gray-700 truncate max-w-xs">
                    {file.name}
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full flex items-center mr-2">
                    <CheckIcon className="w-3 h-3 mr-1" />
                    {translations.success[language as keyof typeof translations.success]}
                  </span>
                  <button onClick={() => removeFile(index)} className="text-gray-500 hover:text-red-500">
                    <XIcon className="w-5 h-5" />
                  </button>
                </div>
              </li>)}
          </ul>
        </div>}
    </div>;
};