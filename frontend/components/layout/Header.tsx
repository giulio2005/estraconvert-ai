'use client';

import Link from 'next/link';
import { FileSpreadsheet } from 'lucide-react';

export default function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <FileSpreadsheet className="text-white" size={20} />
            </div>
            <h1 className="text-xl font-semibold text-gray-900">EstraConvert</h1>
          </Link>
          <nav className="hidden md:flex items-center space-x-8">
            <Link href="/" className="text-gray-600 hover:text-gray-900 transition-colors">
              Home
            </Link>
            <Link href="/convert" className="text-gray-600 hover:text-gray-900 transition-colors">
              Converti
            </Link>
            <span className="text-gray-600 hover:text-gray-900 transition-colors cursor-pointer">
              Supporto
            </span>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
              Accedi
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}
